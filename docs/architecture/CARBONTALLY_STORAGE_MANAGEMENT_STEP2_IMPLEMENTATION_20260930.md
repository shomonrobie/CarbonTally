# CarbonTally — Storage Management Step 2 — Implementation Report

**Document ID:** CT-STORAGE-MANAGEMENT-STEP2-20260930-001
**Repository:** `ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Base HEAD:** `cabdca8380415e73a25cf23eb393d0b15c0af391`
**Date:** 2026-09-30
**Predecessor:** `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP1_IMPLEMENTATION_20260930.md` (Step 1 — **CLOSED**, verified together with Step 2)
**Scope:** Step 2 only — the completion layer over Step 1's secure-upload foundation.
**Status:** **STORAGE MANAGEMENT STEP 2 — CLOSED** (with Step 1) — see the closure record in §20.
Recorded in `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.4.

## Governance rules observed

| Rule | How it was observed |
|---|---|
| Read the governance set before changing code | Read `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md`, `CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md`, `CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md`, `docs/cline/CARBONTALLY_CONSULTANT_CLIENT_DECISION_RECOVERY_20260930.md` and the Step 1 report. |
| Ratified decisions not reopened; no new product decisions | Step 2 implements only what existing ratified material supports. Two sub-items the repository does **not** answer (physical destruction of rejected/orphaned objects; per-consultant managed-client capacity expansion) are reported as unresolved (§10, §13, §16) instead of being invented. |
| No consultant storage tenancy / no consultant bucket / client ownership unchanged | Every object remains under `uploads/{client_organization_id}/…` in the private `documents` bucket. No consultant id appears in any key. Verified by test. |
| No clone/copy/export/move/re-import on relationship change | No Step 2 code copies, moves or deletes bytes. An ended consultant grant causes a **denial**, never a data movement. Verified by test. |
| Preserve existing uncommitted work | No `git reset` / `git clean` / `git stash` / destructive checkout was run. Only the files in §3 were added or edited. |
| No commit / push / deploy / production migration / production data mutation | None performed. The Step 2 migration is prepared only (§17). |

---

## 1. Scope — exactly what Step 2 implemented

| Step | Item | Outcome |
|---|---|---|
| 2A | Frontend / browser adoption of the direct-upload flow | **Implemented** — the V3 customer Documents page and the consultant workspace upload through signed direct-to-storage URLs, with progress, precise error reporting and the backend's real verdict. The previous multipart helpers remain exported for compatibility. |
| 2B | Legacy upload paths | **Implemented** — `/api/upload`, `/api/organizations/{org}/files/upload` and `/api/repair-pdf` authorize through the single upload gate, run the security gate **before any write**, write canonical tenant-scoped keys, and never construct a public URL. |
| 2C | Retire `get_public_url()` for documents | **Implemented** — the three document-storage call sites are gone; document responses carry short-lived signed URLs and durable records store the canonical path. |
| 2D | External malware scanning | **Implemented as a configured boundary; no vendor installed.** Explicit scanner configuration, a provider registry, a finer-grained scanner state machine and a fail-closed requirement switch. No repository evidence of an approved provider exists, so none was invented. |
| 2E | Rejected-object disposition | **Safe lifecycle only** — quarantine (`rejected`) is terminal, non-processable and non-downloadable. Physical deletion of rejected objects is **not authorized by any repository rule** and was not implemented; the gap is recorded in code (`services.document_cleanup.physical_disposition_policy()`) and in §10. |
| 2F | Abandoned-upload cleanup | **Implemented** — idempotent, audited, non-destructive reaping of abandoned `pending_upload` rows to the terminal `upload_expired` state, bounded by Step 1's existing 24 h completion window and wired into the existing retention entry point. |
| 2G | Storage retention / lifecycle | **Inspected, aligned, not extended** — enforcement remains the configured-only `document_retention_days` rule; Step 2 adds no duration and no new retention domain. |
| 2H | Storage access model / RLS | **No RLS change required or made.** Backend-authorized signed access is preserved; the D32 predicates are untouched (§7). |
| 2I | Storage-layer file-size limit | **Migration prepared** (not applied): the `documents` bucket limit is aligned to the ratified 10 MiB in either direction, because CT-FINAL-01's migration only tightens and therefore could not correct a lower live limit. |
| 2J | OCR / direct-upload processing parity | **Implemented** — the completion path reads the verified object once (bounded by the effective limit) and hands the same bytes to the shared pipeline, so page count and OCR prefill match a proxied upload. |
| 2K | Consultant provenance | **Implemented/verified** — client-org ownership, consultant firm/member provenance, uploader, timestamps and audit; relationship end denies access without moving bytes. |
| 2L | Audit completion | **Implemented** — new audited actions for abandoned-upload reaping, cleanup passes, scanner-unavailable and derived-artefact creation, on top of Step 1's set. No secret is ever persisted. |
| 2M | Report-artifact storage | **Verified complete in code; provisioning remains operational.** The private `report-artifacts` model, ratified key, append-only and SHA-256 integrity semantics are exercised by test; no Step 2 change was needed and none was made. |
| 2N | Storage quota / capacity | **Integrated with the existing commercial model** — accepted uploads refresh the existing `billing_storage_usage` metering snapshot that feeds the admin-configurable `billing_plans.included_storage_bytes`. No parallel entitlement system; no upload refusal invented (§13). |
| 2O | Document access / download | **Verified** — every read surface follows authenticated actor → organization/consultant authorization → lifecycle/security state → short-lived signed URL; signed URLs are never persisted. |
| 2P | Original vs derived documents | **Implemented** — a dedicated derived-artefact key namespace (`uploads/{org}/derived/{uuid}`), explicit derived provenance on the repair utility, and no server-side compression of oversized originals. |
| 2Q | Legacy prefixes / object inventory | **Assessed; bounded migration of NEW writes only** (§7). No production object was moved or deleted. |
| 2R | Security review | Performed against actual code; findings in §18 and in the architecture document. |
| 2S | Testing | Step 1 tests + new Step 2 tests + touched-surface tests + full unit suite (§14/§15) and a new frontend suite (§14). |
| 2T | Documentation | This report + `CARBONTALLY_STORAGE_MANAGEMENT_ARCHITECTURE.md`. |
| 2U | Migration / deployment boundary | One prepared migration; explicitly unapplied (§17). |

## 2. Step 1 compatibility — how Step 2 preserves Step 1

* **The single upload gate keeps its role.** Every ingress still authorizes through `api.upload_gate`; Step 2 *widened its use* to the legacy routes instead of adding a second authorization model.
* **Storage keys are unchanged and single-sourced.** `services.storage_keys.build_document_storage_key()` still produces `uploads/{org}/{YYYY}/{MM}/{DD}/{uuid}{.ext}`; the derived-artefact builder is additive and cannot produce a document key.
* **The lifecycle is extended, never weakened.** `pending_upload → security_check_pending → clean | rejected` is intact; the new `upload_expired` state is terminal and blocked from both processing and download.
* **Fail-closed predicates are preserved.** `is_processable` / `is_downloadable` still deny `pending_upload` and `rejected`; `upload_expired` was added to the blocked set.
* **The structural scanner still always runs and still never claims an external scan.** The Step 2 scanner states are additive; `virus_scanned` is only ever true when an external provider actually returned a verdict.
* **The original object is still never rewritten.** `services.storage` still exposes no update/upsert/remove surface (asserted by test) and the derived path writes a separate object.
* **Step 1's suite still passes unchanged in behaviour.** The only test-side change is additive: the Step 1 test double now also implements the reader Step 2's completion path uses (`download_object`), while the `download_object_prefix` name is still provided so no Step 1 assertion changes (§3.2).

## 3. Files changed

### 3.1 New files

| File | Purpose |
|---|---|
| `backend/services/document_cleanup.py` | Step 2E/2F/2G — abandoned-upload reaping (idempotent, audited, non-destructive) and the explicit statement of the unresolved physical-disposition requirement. |
| `backend/services/storage_metering.py` | Step 2N — integrates accepted uploads with the EXISTING metering/entitlement model; records exactly what is and is not integrated. |
| `backend/tests/unit/api/test_storage_management_step2.py` | The Step 2 test suite (41 tests). |
| `frontend/src/v3/__tests__/direct-upload.test.js` | Step 2A browser-contract tests (14 tests). |
| `supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql` | Step 2I — storage-layer limit alignment (prepared, **not applied**). |
| `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_ARCHITECTURE.md` | Step 2T — the final storage-management architecture document. |
| `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md` | This report. |

### 3.2 Edited files

| File | Change |
|---|---|
| `backend/services/document_security.py` | Step 2D/2F: `STATUS_UPLOAD_EXPIRED` (+ transitions / blocked set); scanner result states (`SCAN_STATES`), `SCANNER_REQUIRED_ENV_VAR`, a provider registry (`register_scanner` / `installed_scanners`), `external_scan_required()` / `external_scan_status()`, `ScanVerdict.scan_state` / `external_scan_required` / `scanner_error`, `external_scan_claimed()` and `as_scanner_unavailable()` / `as_scanner_error()`; `scan_document()` now fails closed when a required external scan is unavailable and never lets a scanner exception escape. |
| `backend/services/storage.py` | Added `download_object()` (bounded full read for Step 2J parity). No existing function changed. |
| `backend/services/storage_keys.py` | Added the derived-artefact builder (`build_derived_artifact_key`, `is_derived_artifact_key`, `DERIVED_KEY_SEGMENT`). |
| `backend/services/retention.py` | Wired the abandoned-upload reap into the existing enforcement entry point (bounded by the existing completion window, not a new duration). |
| `backend/data/organization_files.py` | Added `list_abandoned_pending_uploads()` (read-only). |
| `backend/api/upload_gate.py` | Added the Step 2 audit actions (`document.upload_authorisation_expired`, `document.cleanup`, `document.security_scan_unavailable`, `document.derived_artefact_created`). |
| `backend/api/v3_document_uploads.py` | Step 2D/2J/2N: full-object read feeding both the gate and the pipeline, scan-state/scanner reporting in the start and completion responses, the scanner-unavailable audit event, and best-effort storage metering after acceptance. |
| `backend/routes/upload.py` | Step 2B/2C/2P: `POST /api/upload` and `POST /api/repair-pdf` authorize through the gate, run the security gate before writing, use canonical / derived tenant keys, return signed URLs, and record the security verdict plus derived provenance (`derived: true`, `original_replaced: false`). |
| `backend/routes/organizations/files.py` | Step 2B/2C/2Q: `POST /api/organizations/{org}/files/upload` uses the gate, the security gate, the canonical key and a signed URL; the legacy org-less key builder is no longer called by that route. |
| `frontend/src/v3/api.js` | Step 2A: `v3StartDirectUpload`, `v3CompleteDirectUpload`, `putBytesToSignedUrl` (progress + abort), `v3UploadDocumentDirect`, the consultant equivalents, and machine-readable error codes (`UPLOAD_TOO_LARGE`, `UPLOAD_UNSUPPORTED_TYPE`, `UPLOAD_SECURITY_REJECTED`, `UPLOAD_AUTHORIZATION_EXPIRED`, `UPLOAD_STORAGE`, `UPLOAD_NETWORK`); `uploadConsultantDocument` now uses the direct flow with an unchanged signature and payload shape. |
| `frontend/src/v3/customer/DocumentsPage.jsx` | Step 2A: the upload control uses the direct flow with progress, an accepted-type hint and outcome copy that reports the backend's verdict. |
| `frontend/src/v3/consultant/ConsultantPage.jsx` | Step 2A: consultant upload errors/notices reflect the backend's real verdict. |
| `backend/tests/unit/api/fakes.py` | The in-memory files fake mirrors `list_abandoned_pending_uploads` (Step 2F). |
| `backend/tests/unit/api/test_storage_management_step1.py` | The Step 1 `_FakeStorage`/fixture now also provides `download_object` (the reader Step 2's completion path uses) in addition to `download_object_prefix`. No Step 1 assertion was changed, weakened or removed. |

## 4. Upload architecture — the exact final flow

```text
Customer / Consultant browser
  |
  | 1. POST /api/v3/documents/upload-url
  |    or POST /api/v3/consultants/clients/{client_id}/documents/upload-url
  |    (JSON metadata only: filename, size_bytes, content_type, data_type)
  v
CarbonTally backend  (api/v3_document_uploads.py)
  |
  | 2. api.upload_gate authorizes the actor:
  |      org member   -> require_org_member + ensure_org_access (+ CL-42 viewer denial)
  |      consultant   -> require_consultant + ACTIVE client grant (D15) + can_upload_documents
  |    -> UploadActor with the CLIENT organisation id as the storage tenant
  |
  | 3. upload policy (utils.upload_limits.resolve_policy) validates extension + declared size
  | 4. services.storage_keys generates the object key (never a client-supplied path)
  | 5. organization_files row created as `pending_upload` (client org, provenance metadata)
  | 6. services.storage.create_signed_upload_url issues a short-lived, object-scoped URL
  v
Browser  -> PUT bytes  ->  private Supabase Storage (`documents`, key `uploads/{org}/…`)
  |
  | 7. POST …/upload-complete
  v
CarbonTally backend
  |
  | 8. re-authorize; re-check the tenant prefix of the stored key
  | 9. verify the object exists and read its REAL size (rejects empty/oversized)
  |10. read the object back once (bounded by the effective limit)
  |11. run the security gate -> clean | rejected (quarantined)
  |12. on clean: status `clean`, audit, enqueue into the EXISTING durable pipeline
  |    (extraction batch/item -> document_processing_queue -> OCR prefill)
  |    and refresh the EXISTING storage-metering snapshot
  v
normal CarbonTally processing
```

Key properties (all test-asserted):

* the browser receives **only** an object-scoped short-lived authorisation — no service-role key, no project secret, no user-JWT storage credential;
* the backend **never proxies the ordinary upload byte stream** (the multipart V3 endpoint is retained for compatibility but is no longer used by the browser);
* a document that has not passed the gate is never downloadable and never enqueued;
* resumable/TUS is refused with a stated reason (a TUS session would require exposing a storage credential to the browser).

## 5. Security — authorization and the malware/security lifecycle

### 5.1 Authorization (unchanged single model, now applied everywhere)

| Ingress | Authorization |
|---|---|
| `POST /api/v3/documents/upload-url` + `…/upload-complete` | `require_org_member()` → `api.upload_gate.authorize_organization_upload()` (viewer read-only denial, `ensure_org_access`, PE denial) |
| `POST /api/v3/consultants/clients/{id}/documents/upload-url` + `…/upload-complete` | `require_consultant()` → active client grant (`consultant_clients`, D15) → firm ownership → `can_upload_documents` |
| `POST /api/v3/uploads` (multipart, retained) | the same gate (Step 1) |
| `POST /api/upload` (legacy) | **Step 2** — the same gate, plus the pre-existing body-scope rule |
| `POST /api/organizations/{org}/files/upload` (legacy) | **Step 2** — the same gate (replacing the route-local equality check) |
| `POST /api/repair-pdf` (legacy utility) | **Step 2** — the same gate (caller's own organisation) |
| `GET /api/v3/documents/{id}/signed-url` | the same gate + lifecycle/security state |

### 5.2 Lifecycle state machine (as implemented)

```text
pending_upload ──► security_check_pending ──► clean ──► processing ──► failed
      │                     │                  │
      │                     └──► rejected      └──► (terminal gate outcome)
      ├──► rejected                (quarantined: never downloaded, never processed)
      └──► upload_expired          (Step 2F: terminal, never completed/downloaded/processed)
```

* `is_processable()` denies `pending_upload`, `rejected`, `upload_expired`.
* `is_downloadable()` denies `pending_upload`, `rejected`, `upload_expired` (and `security_check_pending`).
* Only a CLEAN verdict enqueues the processing pipeline; a rejection or an expired authorisation never does.

### 5.3 Scanner result states (Step 2D)

`clean` · `malware` · `structural_rejection` · `scanner_unavailable` · `scanner_error` — recorded on `organization_files.metadata.security_gate` and returned to the caller.

**A document is accepted only on `scan_state = clean`.** `scanner_unavailable` and `scanner_error` are fail-closed: when `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED` is true and no installed provider can return an external verdict, the document is **quarantined** (and audited as `document.security_scan_unavailable`) rather than accepted. A scanner that raises does not propagate an exception into the upload path — it produces a rejection.

## 6. Legacy paths — migrated, retained, deprecated or intentionally left

| Path | Step 2 disposition | Evidence |
|---|---|---|
| `POST /api/v3/uploads` (multipart V3) | **Retained** (compatibility + internal callers). Still gated by Step 1's gate, security gate and canonical key. The browser no longer uses it. | `api/v3_documents.py`; Step 1 suite; Step 2 frontend suite asserts the browser path changed. |
| `POST /api/upload` (legacy proxied) | **Hardened.** Same gate; security gate before any write; canonical `uploads/{org}/…` key; signed URL instead of a public URL; verdict + provenance recorded on the row; the `manual_review_queue.file_url` column now receives the canonical path (never a public/signed URL). | `routes/upload.py`; Step 2 tests (rejection writes nothing; canonical key; signed URL). |
| `POST /api/organizations/{org}/files/upload` | **Hardened.** Same gate; security gate before any write; canonical key (the org-less `organizations/{org}/…` prefix is no longer used by this route); signed URL; verdict recorded. | `routes/organizations/files.py`; Step 2 tests. |
| `POST /api/organizations/files/bulk` | **Retained, intentionally unchanged.** It remains a legacy batch ingress with its own limits enforcement; the legacy key helper it uses is left in place. It is **not** in the current frontend's upload path. Recorded as a residual item in §16 rather than silently rewritten. | `routes/organizations/files.py` (`bulk_upload_files`). |
| `POST /api/repair-pdf` | **Retained as a derived-artefact utility and hardened.** Gate + input security scan; output written under the client organisation's namespace as a *derived* object; signed URL; explicit `derived`/`transformation`/`original_replaced` provenance. The legacy org-less `repaired_pdfs/…` prefix is no longer used for **new** objects. Note the frontend callers of this utility point at `/repair-pdf` (not the `/api`-prefixed route) — see §16. | `routes/upload.py`; Step 2 source assertions. |
| `POST /api/upload-batch` | **Left intentionally.** It already returns a "premium feature" refusal and writes nothing. | `routes/upload.py`. |

No legacy route now stores content that bypasses the security gate and then feeds normal processing.

## 7. Storage — buckets, keys, RLS, signed URLs, lifecycle

### 7.1 Buckets

| Bucket | Public | Purpose | Step 2 change |
|---|---|---|---|
| `documents` | **private** (D32) | every customer/consultant-uploaded document and derived artefact | none to the bucket's privacy; the per-file size limit is aligned by a prepared migration (§8) |
| `report-artifacts` | **private** (B4-D6) | frozen report PDFs | **none** (§12) |

No bucket was made public, no bucket was created, and no consultant bucket exists.

### 7.2 Object keys

| Kind | Layout | Builder |
|---|---|---|
| Document (canonical) | `uploads/{organization_id}/{YYYY}/{MM}/{DD}/{uuid4_hex}{.ext}` | `services.storage_keys.build_document_storage_key` |
| Derived artefact (Step 2P) | `uploads/{organization_id}/derived/{uuid4_hex}{.ext}` | `services.storage_keys.build_derived_artifact_key` |
| Report artefact (ratified, unchanged) | `{organization_id}/{report_id}/{report_version_id}.pdf` in `report-artifacts` | `domain.report_artefact.object_key_for` |

The tenant segment is validated (UUID or safe single-segment token) so a caller can never inject a path segment. The user's file name is provenance only and never determines path identity.

### 7.3 Storage RLS — what protects what (Step 2H)

**What storage RLS protects:** the `documents` bucket's four D32 policies grant `authenticated` access only when `bucket_id = 'documents'`, `foldername(name)[1] = 'uploads'` **and** `foldername(name)[2]::uuid` is one of the caller's active `organization_members` rows. That is the defence for any *direct user-JWT* storage access, and it stays exactly as ratified (asserted by test — no consultant branch was added).

**What backend authorization protects:** actor identity, organisation/consultant scope, capability, entitlement, upload policy and the document security lifecycle. The browser only ever receives a signed URL that the backend issued *after* those checks.

**Why the combined model is secure:** the application never requires direct user-JWT storage access — the direct flow uses object-scoped signed upload URLs, and downloads use short-lived signed URLs issued by the backend. Expressing consultant access as an RLS branch would create a second authorization system; consultant access is instead authorized against the client organisation through the backend relationship/capability model, which is what the ratified architecture requires.

**Residual RLS limitations (documented, not changed):** Storage RLS does not model `organization_files` lifecycle state (a rejected document's object would still be addressable by a *user-JWT* storage read if that path were ever opened); the application-layer gate is the enforcement point and the frontend does not use that path. Unchanged from Step 1; restated in the architecture document.

### 7.4 Signed URLs

* **Upload:** short-lived (900 s), object-scoped, signed by the backend with the service-role client; the browser receives no credential.
* **Download/preview:** short-lived (3600 s), issued only after authorization **and** the lifecycle/security check; `rejected`, `pending_upload` and `upload_expired` documents are refused with 409.
* **Never persisted:** audit records identifiers and the lifetime only; neither the document row (`path` / `metadata.file_url`) nor `manual_review_queue.file_url` ever stores a signed URL.

### 7.5 Legacy prefixes (Step 2Q inventory)

| Prefix | Producer today | Disposition |
|---|---|---|
| `uploads/{org}/{date}/…` | V3 uploads, direct uploads, hardened legacy `/api/upload` | **canonical** — kept |
| `uploads/{org}/derived/…` | repair utility (new writes) | **new** — canonical + derived marker |
| `organizations/{org}/…` | legacy `get_organization_upload_path` (bulk route only) | **retained for bulk writes only**; outside the D32 RLS predicate, service-role-only; recorded in §16. Existing objects untouched. |
| `repaired_pdfs/…` | legacy repair writes before Step 2 | **no new writes** (new derived objects use the tenant namespace); existing objects untouched — nothing deleted or moved |
| `batches/…`, `manual_review/…` | no current producer found in the upload paths | **untouched** — no objects moved or deleted |

No production object was moved, copied, renamed or deleted by Step 2.

## 8. Limits — application and storage layer

| Layer | Value | Where |
|---|---|---|
| Ratified platform cap | **10 MB per file** (50 files/batch, 500 MB/batch) | `backend/utils/upload_limits.py` `PLATFORM_MAX_*` |
| Effective out-of-the-box default | **6 MB per file** | `DEFAULT_MAX_FILE_SIZE_MB`, admin-configurable up to the cap |
| Storage layer (code, prepared) | `documents.file_size_limit = 10485760`, private | `20261025000000_ct_step2_documents_bucket_size_alignment.sql` (**not applied**) |
| Storage layer (live environment) | **unchanged by Step 2** — the PO evidence review recorded 2 MiB | deployment dependency (§17) |

Step 2 changes no product limit. It aligns the storage layer with the ratified cap because CT-FINAL-01's migration only tightens (`file_size_limit > ratified_limit`) and therefore could not correct a *lower* live limit; a storage cap below the application limit silently refuses uploads the product says it supports. The historical migration is **not** edited (asserted by test). The per-file limit is not a subscription/client capacity — capacity is the separate existing commercial model in §13.

## 9. Malware scanning — exactly what scans files

**What actually scans a document in this repository today:**

1. `StructuralScanner` — the only installed scanner. It always runs server-side over the stored bytes: extension allow-list, extension↔declared-type agreement, actual magic-byte detection, filename/path safety, empty/truncated detection, the industry-standard EICAR test signature, and PDF active-content markers (reported, never stripped).
2. **Nothing else.** No external malware/virus provider is installed or configured, so **no file is virus-scanned by a vendor** and the platform says so explicitly:
   * `ScanVerdict.scanner = "structural"`,
   * `ScanVerdict.external_scan_available = false`,
   * `security_gate.virus_scanned = false` in the API response and on the document row.

**How an approved provider would be integrated (no vendor invented):** implement the `DocumentScanner` protocol, register it with `services.document_security.register_scanner("<provider-id>", factory)` where the deployment imports it, set `CARBONTALLY_DOCUMENT_SCANNER=<provider-id>`, and — to make the external verdict a precondition for processing — set `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED=true`. Until a provider is registered and configured, that second switch makes uploads from *any* ingress fail closed into quarantine instead of pretending a scan happened.

**No false claims:** `external_scan_claimed()` is true only when a verdict came from an external provider, and `virus_scanned` is derived from it.

## 10. Retention / cleanup — only what is implemented and authorized

**Implemented and authorized:**

* **Abandoned upload authorisations (Step 2F).** `services.document_cleanup.reap_abandoned_uploads()` transitions rows still in `pending_upload` whose authorisation is older than the existing `UPLOAD_COMPLETION_WINDOW_SECONDS` (24 h) to the terminal `upload_expired` state. It is:
  * **idempotent** — a second pass reports `eligible: 0, changed: 0`;
  * **non-destructive** — `objects_deleted: 0`; the row and its provenance are retained and no object is read, signed or deleted;
  * **audited** — `document.upload_authorisation_expired` per row and `document.cleanup` per pass;
  * **dry-run by default**, and wired into the existing `services.retention.enforce_retention()` entry point used by `backend/tools/enforce_retention.py`.
* **Document retention (pre-existing, unchanged).** `system_settings.document_retention_days` → `expire_documents_older_than()` soft-expires (`deleted_at`); `None` means "not configured" and nothing is purged. Step 2 adds no duration and no new domain. Audit/evidence tables remain explicitly excluded.

**Not implemented because no ratified rule exists (reported, not invented):**

| Item | Status |
|---|---|
| Physical deletion of security-rejected (quarantined) objects | **Not authorized** — `physical_disposition_policy()["rejected_objects"]["physical_deletion"] == "not_authorized"`; Step 2 keeps the safe lifecycle state only and deletes nothing. |
| Orphaned objects with no valid document record | **Not authorized** — no destructive semantics exist; nothing is deleted. |
| Physical deletion of expired `pending_upload` rows/objects | **Not authorized** — only the state change is applied. |

## 11. Consultant provenance — how it survives relationship changes and conversion

| Event | Bytes | Provenance | Access |
|---|---|---|---|
| Consultant uploads for an active client | stored under `uploads/{client_org}/…` in the private `documents` bucket | `organization_files.metadata`: `upload_actor_type=consultant`, `uploaded_by_consultant_firm_id`, `uploaded_by_consultant_role`, `uploaded_by_user_id`, `consultant_originated=true`; row organisation = the client's; audit with `acting_for_organization_id` | consultant + client, both authorized by the backend |
| Consultant relationship ends (grant not active) | **unchanged** — nothing copied, moved, exported or re-imported | unchanged | consultant access **ends** (denied at the gate); client access unaffected |
| Client becomes a direct CarbonTally customer | **unchanged** — same organisation, same objects, same document ids | unchanged (consultant provenance remains on the row and in audit) | client access continues |

No consultant-owned bucket, prefix or namespace exists anywhere in the implementation, and no storage key contains a consultant identifier (both asserted by test).

## 12. Report artifacts — exact status

| Aspect | Status |
|---|---|
| Bucket | `report-artifacts`, **private**; the only bucket permitted for a frozen artefact (B4-D6). |
| Object key | `{organization_id}/{report_id}/{report_version_id}.pdf` — derived, never caller-supplied (`domain.report_artefact.object_key_for`), matching the live `report_version_artifacts` CHECK constraint. |
| Append-only | Enforced by the adapter (a second upload to an existing key raises) and by the existing "already has a frozen artefact with a different hash → refuse" rule. |
| Integrity | SHA-256 lowercase hex, computed at freeze; a mismatch refuses re-finalisation. |
| Access | Short-lived signed URL only (`SIGNED_URL_TTL_SECONDS = 300`); no public URL path exists. |
| Step 2 change | **None.** No Step 2 file writes to this bucket, no document was moved into it, and the Step 2 migration does not touch it (all asserted by test). |
| Provisioning | The bucket is provisioned **operationally** (no migration creates it). `SupabaseReportArtefactStorage.bucket_exists()` is the application-level preflight; absence is reported as `False`, never an exception. |

## 13. Entitlement — what was integrated and what remains separate

**Integrated (existing system, no second entitlement model):**

* an accepted upload refreshes the existing `billing_storage_usage` metering snapshot via `BillingService.meter_storage()` (`services.storage_metering.record_storage_usage`);
* the included allowance is the admin-configurable `billing_plans.included_storage_bytes`; the entitlement view is the existing `BillingService.get_entitlement()["storage"]`;
* metering is **best-effort**: it never fails an accepted upload, and the outcome is reported in the upload response (`storage_metering`).

**Remains separate / deliberately not implemented:**

| Item | Reason |
|---|---|
| Refusing uploads when capacity is exceeded | the ratified model *meters and bills* over-allowance (`additional_bytes`); an upload refusal would be a new commercial policy |
| Per-consultant managed-client capacity | already expressed by the existing plan/subscription model; Step 2 makes no change to it |
| A parallel entitlement/quota system | explicitly out of scope |

## 14. Tests — commands and exact results

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/unit/api/test_storage_management_step2.py -q` | **41 passed, 0 failed (EXIT=0)** |
| `.venv/bin/python -m pytest tests/unit/api/test_storage_management_step1.py tests/unit/api/test_storage_management_step2.py tests/unit/api/test_ct_final_01_upload_limits.py tests/unit/api/test_f05_r1_org_scope_authorization.py tests/unit/api/test_v3_ocr_wiring.py tests/unit/api/test_v3_phase_c_regressions.py tests/unit/api/test_v3_legacy_reimplementation.py tests/unit/api/test_composition_root.py tests/unit/api/test_v3_routes_exposed.py tests/unit/api/test_document_content_type.py tests/unit/api/test_step2_stabilization_enqueue_visibility.py tests/unit/services/test_report_artefact_bucket_preflight.py tests/unit/domain/test_report_artefact.py -q` | **216 passed, 0 failed (EXIT=0)** — the full storage/upload/consultant/report-artefact touched surface, including the entire Step 1 suite |
| `frontend: CI=true npx react-scripts test --watchAll=false --testPathPattern='direct-upload'` | **14 passed, 0 failed (1 suite)** |
| `.venv/bin/python -m pytest tests/unit -q` (full unit suite) | **4621 tests collected; 8 failed** (every failure identified in §15); the remainder passed or skipped. The run's final counts line was not captured because the sandbox terminated the process immediately after the failure summary — the failure list itself is complete and is reproduced in §15. |

Step 2 test coverage (all 26 required categories):

| Required area | Covered by (in `test_storage_management_step2.py`) |
|---|---|
| Frontend/API contract | upload-authorisation payload, direct PUT to the signed URL with declared headers, progress, no credential; browser suite covers start/complete/errors |
| Legacy paths | security gate before any write; canonical key + signed URL; cross-tenant/scoped denials; viewer denial; source hardening assertions |
| Malware scanning | clean, malware, structural rejection, scanner-unavailable (fail-closed), scanner-error, registry, uninstalled-provider honesty, no false claim |
| Lifecycle | pending, expired pending (dry-run + apply + idempotent), rejected/quarantined, clean, terminal-state predicates |
| Access | organisation member, consultant, ended consultant, cross-tenant completion denial, quarantined download refusal |
| Storage | generated key, private bucket, signed URL (not public), expiry declarations, tenant scoping, original integrity |
| Retention/cleanup | reaping bounded by the existing window, non-destructive (`objects_deleted: 0`), audited, idempotent; unresolved physical disposition asserted |
| Report artifacts | private bucket, ratified key, append-only, signed URL, integrity model |
| Limits | 6 MB default, 10 MB cap, alignment migration content, storage-aware no-op, ordering |
| Consultant lifecycle | client ownership + provenance, relationship end denial with no byte movement |

## 15. Full-suite failures

The full unit suite (`pytest tests/unit`) reports **8 failures**, all **pre-existing and unrelated to Step 1 or Step 2** (the same set Step 1 recorded, plus its migration-hygiene family):

| # | Test | Cause | Pre-existing? | Touched by Step 1/2? |
|---|---|---|---|---|
| 1 | `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | discovery API behaviour | Yes (recorded by Step 1) | No |
| 2 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | asserts `len(migrations) == 71`; 92 existed before Step 2 | Yes | No — **verified by re-running with the Step 2 migration temporarily moved aside: the test still failed (and still counted 92 files).** |
| 3 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | asserts an exact short list of migrations after the I1 migration; later P8/CT migrations already existed | Yes | No — same controlled re-run: still failed without the Step 2 migration |
| 4 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | expects `20261007000000_…` to be the last migration; `20261008000000…20261024000000` already existed | Yes | No — same controlled re-run |
| 5 | `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | fails on `20261023000000_ct02_scheduled_reporting.sql` (already present) | Yes | No — same controlled re-run |
| 6-8 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice`, `::test_suggest_missing_fields_leave_unresolved`, `::test_suggest_no_fabrication_on_garbage` | extraction-suggestion date normalisation | Yes (recorded by Step 1) | No |

The verification method for the migration-hygiene group matters and is recorded: the Step 2 migration file was temporarily moved out of `supabase/migrations/`, the four hygiene tests were re-run (they failed identically, with the same stale expectations), and the file was restored byte-for-byte. Step 2 therefore introduces **no new failure** and turns **no passing test into a failing one**.

## 16. Deferred items (not implemented)

| Item | Why |
|---|---|
| External malware-scan vendor integration | no approved provider exists in the repository; inventing one is out of scope. The boundary, states and fail-closed configuration are complete (§9). |
| Physical destruction of rejected / orphaned / expired objects | no ratified retention/destruction rule exists (§10). |
| Applying the storage-layer alignment migration | production deployment is not authorized (§17). |
| Storage-layer lifecycle (auto-expiry) configuration | requires an explicit retention decision plus provider configuration. |
| Per-consultant managed-client capacity expansion | outside the existing subscription scope. |
| The legacy `/api/organizations/files/bulk` ingress's legacy key helper | retained intentionally; not in the current frontend upload path. |
| `PDFRepairTool` / `PDFIngestionPortal` route prefix | they call `/repair-pdf` rather than `/api/repair-pdf` — a pre-existing frontend routing defect, out of Step 2 scope. |
| Registering the derived repair artefact as a document row | would introduce new record semantics; the utility returns explicit provenance instead. |
| A true range read for the completion probe | the bounded full read is acceptable at the 10 MiB cap. |
| Removal of any legacy route | no repository evidence establishes deletion is safe; all legacy routes were retained and hardened. |

## 17. Deployment requirements (nothing below was executed)

| # | Requirement | Status |
|---|---|---|
| 1 | Apply `supabase/migrations/20261025000000_ct_step2_documents_bucket_size_alignment.sql` to each environment | **Code/migration prepared — NOT applied.** The live `documents` bucket may therefore still refuse uploads between the live limit (recorded at 2 MiB by the PO evidence review) and the application limit (6 MB effective / 10 MB cap). |
| 2 | Apply `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` where it is still unapplied | **Pre-existing deployment gap** (recorded by Step 1). |
| 3 | Configure `CARBONTALLY_DOCUMENT_SCANNER` (+ `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED` where an external scan must be mandatory) and install the corresponding provider adapter | **Not configured** — the platform runs the structural gate only and says so. |
| 4 | Provision the private `report-artifacts` bucket | operational (pre-existing); no Step 2 change. |
| 5 | Deploy the updated backend + frontend code | **Not deployed.** |
| 6 | Schedule the existing retention/cleanup entry point (`backend/tools/enforce_retention.py`) so abandoned-upload reaping runs | **Not scheduled** by this task; the tool is dry-run by default. |

**Environment actually changed by Step 2: none.** No migration was applied, no bucket configuration was altered, no object was written, moved or deleted, and no production/shared data was mutated.

## 18. Risks (evidence-backed only)

1. **The live storage-layer cap may still be below the application limit** until §17 requirement 1 is applied — a valid file between those two values would be refused by Storage (not by the application). Evidence: the PO evidence review's 2 MiB reading and the CT-FINAL-01 migration's tighten-only predicate.
2. **No malware scanner is installed**, so the gate is structural only. This is disclosed in every verdict, response and document row (`virus_scanned: false`) rather than hidden. Enabling `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED` before installing a provider would quarantine all uploads — fail-closed by design.
3. **Security-rejected objects remain physically present** in the client's namespace (logically quarantined): not processable and not downloadable through any application path, but their physical disposition awaits a ratified rule.
4. **Direct uploads cannot overwrite**: the browser PUTs with `x-upsert: false` to a server-generated, tenant-scoped, unique key.
5. **A legacy batch ingress (`/api/organizations/files/bulk-upload`) still writes to the legacy `organizations/{org}/…` prefix**, which sits outside the D32 RLS predicate (service-role access only). It is not in the current frontend upload path; removing it would require evidence that no consumer depends on it.
6. **Frontend repair-tool routing** (`/repair-pdf` vs `/api/repair-pdf`) is a pre-existing defect that means that tool is already non-functional from the browser; Step 2 hardened the route but did not change the frontend path.
7. **Direct uploads create the row before the object exists.** An abandoned upload used to leave a permanently `pending_upload` row; Step 2's reaping now resolves such rows to a terminal state (idempotent, non-destructive), so the risk is bounded and visible.

## 19. Final status

Step 2 is complete within its authorized scope: every item in Step 2A–2U is either implemented and tested, or explicitly reported as deferred/unresolved with the reason and the exact dependency. No ratified decision was reopened, no new product policy was invented, no consultant tenancy or bucket was created, no data was moved, and nothing was deployed, committed, pushed or applied.

**STORAGE MANAGEMENT STEPS 1 + 2 — CLOSED** — closure record in §20.

## 20. Closure record — Storage Management Steps 1 + 2 — CLOSED

**STORAGE MANAGEMENT STEPS 1 + 2 — CLOSED.**

| Closure test | State |
|---|---|
| Implementation complete (Step 1 + Step 2, items 2A–2U) | **YES** — §1; every item is implemented or explicitly reported as deferred with its dependency |
| Independent verification complete | **YES** — the combined independent verification of Steps 1 + 2 |
| Verdict | **STORAGE MANAGEMENT — INDEPENDENTLY VERIFIED WITH NON-BLOCKING OBSERVATIONS** |
| Blocking defects | **NONE** |
| Non-blocking observations preserved | **YES** — §20.1; preserved, not hidden, not promoted to requirements |
| Deployment dependencies separated from implementation closure | **YES** — §17 and §20.2 |
| Production deployment | **NOT AUTHORIZED** |
| Storage Step 3 | **NOT AUTHORISED / NOT STARTED** |

The reported verification content: no security bypass that blocks closure; no tenant-isolation
defect; no processing bypass; no false malware-scan claim; direct-upload architecture verified;
consultant authorization verified; storage-key model verified; original evidence integrity verified;
processing parity verified; auditability verified; entitlement/metering integration verified.

The verification report was supplied as an external artefact; it is **not** present in this
repository (there is no `Pasted markdown.md` in the workspace), so this record reproduces the verdict
as reported rather than quoting a repository file. The verdict and the observation list are also
recorded in `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.4.

### 20.1 Non-blocking observations — preserved (verified as NON-BLOCKING / DEFERRED / FOLLOW-UP)

These are recorded exactly as the verification raised them. **None is a Storage Steps 1 + 2 blocker**
and **none is converted into a new requirement or a Storage Step 3** by this closure.

| # | Observation | Classification | Disposition / evidence |
|---|---|---|---|
| 1 | legacy `/api/organizations/files/bulk-upload` uses the legacy `organizations/{org}/…` prefix and lacks the new security gate | **NON-BLOCKING / FOLLOW-UP** (hardening) | re-derived at closure: route at `backend/routes/organizations/files.py:840`; the legacy single-file route *is* gated (`authorize_organization_upload`, line 547). Not in the frontend upload path; removing/re-pathing it needs a dependency inventory (§7, 2Q; §18.5) |
| 2 | legacy download endpoints do not consult document lifecycle state | **NON-BLOCKING / FOLLOW-UP** (hardening) | no new rule is created; the canonical V3 read surfaces do consult lifecycle/security state (2O) |
| 3 | `run_ocr` lacks a lifecycle guard | **NON-BLOCKING / FOLLOW-UP** (hardening) | `backend/api/v3_documents.py:744`; unchanged by this closure |
| 4 | one legacy upload path records `status='uploaded'` | **NON-BLOCKING / FOLLOW-UP** (legacy vocabulary) | `services/document_security.py` carries `LEGACY_STATUS_UPLOADED` for compatibility; the canonical lifecycle (`pending_upload → security_check_pending → clean \| rejected`, plus terminal `upload_expired`) is unaffected |
| 5 | WEBP detection has a dead detection branch | **NON-BLOCKING / FOLLOW-UP** (defect, non-security) | detection vocabulary in `services/document_security.py`; no security outcome depends on it |
| 6 | signed-upload TTL is declarative rather than backend-enforced by Supabase | **NON-BLOCKING / DESIGN CONSTRAINT** (documented) | the declared TTL is surfaced in the upload-authorisation response (`api/v3_document_uploads.py`); per-object key/authorisation remain server-issued |
| 7 | pre-existing unrelated legacy defects | **NON-BLOCKING / PRE-EXISTING** | not caused by, and not in scope of, the storage work |
| 8 | external malware scanner is not installed | **DEFERRED / OPERATIONAL** (deployment dependency) | 2D; the gate is structural only and says so in every verdict (`virus_scanned: false`); enabling `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED` before a provider is registered fails closed |
| 9 | the 10 MiB storage migration is prepared but unapplied | **DEFERRED / DEPLOYMENT DEPENDENCY** | §17 requirements 1–2; the live bucket may still hold a lower cap |
| 10 | `report-artifacts` bucket provisioning remains an operational deployment task | **DEFERRED / OPERATIONAL** | 2M; §17 requirement 4; `bucket_exists()` is the application preflight |

Notes on preservation discipline:

* the observations were **not** deleted, reworded into requirements, or hidden; item 1's route name
  was additionally re-derived at closure and the earlier shorthand in §18.5 is corrected to the real
  route name `/api/organizations/files/bulk-upload`;
* no implementation file was modified to "remove" an observation, and no observation was fixed in
  this closure task (documentation-only task);
* observations 8–10 are **deployment/operational dependencies**, not implementation gaps — they do
  not qualify closure and they do not block it.

### 20.2 Implementation closure vs deployment dependencies (kept separate)

| Class | Items |
|---|---|
| **Implementation closure** (this record) | Storage Step 1 + Step 2 code, tests and documentation; §1 items 2A–2U |
| **Deployment dependencies** (not part of closure) | §17 items 1–6 — applying the two storage-limit migrations, installing/configuring an external scanner provider, provisioning the `report-artifacts` bucket, deploying the backend + frontend, scheduling the existing retention/cleanup entry point |
| **Operational / pre-existing** | §17 items 4 and 6 (`report-artifacts` provisioning, cleanup scheduling) |
| **Not authorised** | Storage Step 3; production deployment; any object movement or deletion; any bucket change |
| **Environment actually changed** | **none** (§17) |

### 20.3 Governance statement for this closure

* This was a **documentation/governance closure only**: no code, migration, bucket, credential,
  environment or shared data was modified, and the pre-existing dirty working tree was **not**
  reset, cleaned, stashed or checked out.
* The closure **does not claim production deployment**: production remains **NOT AUTHORIZED**, and no
  commit or push was performed.
* The authoritative decisions behind this closure — the consultant/client decisions U-1…U-7, the
  capacity decision E-4 and the storage governance decisions S-1…S-3 — are recorded in
  `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41, with the status reconciliation in §41.5.
* The closure was reached on the **reported** independent-verification verdict (§20) and preserves
  the non-blocking observations in §20.1 without turning any of them into a requirement.


