# CarbonTally — Storage Management Step 1 — Implementation & Verification Report

**Document ID:** CT-STORAGE-MANAGEMENT-STEP1-20260930-001
**Repository:** `ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Base HEAD:** `cabdca8380415e73a25cf23eb393d0b15c0af391`
**Date:** 2026-09-30
**Scope:** Step 1 only — the secure document-upload foundation.
**Status:** **STORAGE MANAGEMENT STEP 1 — CLOSED** (verified together with Step 2). Implementation
complete · independent verification complete · no blocking defects · non-blocking observations
preserved (Step 2 report §20) · deployment dependencies separated from implementation closure ·
production deployment **NOT AUTHORIZED**. Recorded in
`CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.4.

## 0. Authority and constraints observed

| Rule | How it was observed |
|---|---|
| Read the governance set before changing code | Read `CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md`, `CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md`, `CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md`, and `CARBONTALLY_CONSULTANT_CLIENT_DECISION_RECOVERY_20260930.md` first. |
| Product Owner decisions are authoritative; ratified decisions not reopened | The ratified consultant/client, commercial and storage decisions in the Step 1 brief are implemented exactly as stated; no decision was re-litigated. |
| No new consultant storage tenancy / bucket / data model | Every object stays under `uploads/{client_organization_id}/…` in the existing private `documents` bucket. No consultant id appears in any path; consultant provenance is application metadata + audit only. |
| No clone / move / copy / export / re-import on relationship change | Nothing in this change copies, moves or deletes bytes; the completion path and the relationship checks are read-only with respect to existing objects. Covered by a test. |
| Preserve existing uncommitted work | No `git reset/clean/stash/checkout` was run. Only the files listed in §1 were added or edited. |
| Production deployment NOT AUTHORIZED | No deployment, no migration application, no bucket change, no production data mutation. |

---

## 1. Implemented — exact files changed

### 1.1 New files

| File | Purpose |
|---|---|
| `backend/services/storage_keys.py` | Server-generated document object keys, filename safety, tenant-token validation, key↔tenant checking. |
| `backend/services/document_security.py` | The document security lifecycle (statuses + permitted transitions) and the scanning boundary: `StructuralScanner` (always runs), scanner resolution/configuration, `ScanVerdict`/`ScanFinding`, `is_processable`, `is_downloadable`. |
| `backend/api/upload_gate.py` | The **single authoritative upload authorization gate** for every ingress, plus the shared significant-document audit emitter. |
| `backend/api/v3_document_uploads.py` | The direct-to-storage (signed upload URL) endpoints for organisation users and consultants, including completion verification. |
| `backend/tests/unit/api/test_storage_management_step1.py` | The Step 1 test suite (30 tests). |
| `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_STEP1_IMPLEMENTATION_20260930.md` | This report. |

### 1.2 Edited files

| File | Change |
|---|---|
| `backend/services/storage.py` | Added `create_signed_upload_url()`, `object_info()`, `object_exists()`, `stored_object_size()`, `download_object_prefix()`, `SIGNED_UPLOAD_TTL_SECONDS`, `UPLOAD_COMPLETION_WINDOW_SECONDS`. Module docstring updated. No existing function changed. |
| `backend/api/v3_documents.py` | `POST /api/v3/uploads` now authorizes through the shared gate; `create_document_and_enqueue` validates + runs the security gate **before** any write, generates the key server-side, records `status=clean`, records the canonical **path** (never a signed URL) in metadata, emits audit events, and delegates the pipeline registration to the new reusable `enqueue_document_processing()` (`content=None` supported for direct uploads). `GET /api/v3/documents/{id}/signed-url` now delegates authorization to the gate, refuses uncleared/quarantined documents, and audits signed-URL issuance. |
| `backend/api/v3_consultants.py` | `POST /api/v3/consultants/clients/{client_id}/documents` now authorizes through the shared gate and passes consultant provenance into the document + audit trail. |
| `backend/api/router.py` | Registers the new upload router. |
| `backend/data/organization_files.py` | `create(..., status=...)` (default stays `'uploaded'`); `update_status(..., size_bytes=...)` to record the platform-verified size. |
| `backend/tests/unit/api/fakes.py` | `MemoryFiles` mirrors the extended repository contract (`status` on create, `update_status`, mapping-aware `update_metadata`, `uploaded_at`). |

---

## 2. Step 1A — implementation map of the existing upload flows (pre-change)

Traced read-only before any edit:

| # | Ingress | Route | Storage write (before) | Authorization (before) | Pipeline |
|---|---|---|---|---|---|
| 1 | V3 canonical (org) | `POST /api/v3/uploads` → `v3_documents.create_document_and_enqueue` | service-role `upload()`, backend-proxied bytes, key `uploads/{org}/{YYYY/MM/DD}/{uuid}_{filename}` | `require_org_member()` + `ensure_org_access` + inline viewer 403 | extraction item + `document_processing_queue` + OCR prefill |
| 2 | V3 consultant | `POST /api/v3/consultants/clients/{id}/documents` → same function | same | `require_consultant` + `_authorized_client_org` + `can_upload_documents` | same |
| 3 | Legacy | `POST /api/upload` (`routes/upload.py:637`) | `get_public_url()` + service-role upload | `require_org_member()` + `enforce_org_body_scope` | legacy |
| 4 | Legacy | `POST /api/organizations/{org}/files/upload` (`routes/organizations/files.py:516`) | `get_public_url()` | `require_org_member()` + inline org compare | legacy |
| 5 | Legacy | `POST /api/repair-pdf` | `get_public_url()` | legacy | – |
| 6 | Frozen report artefact | report generation → `report-artifacts` | schema-`CHECK` key `{org}/{report}/{version}.pdf` | ratified B4-D5/D6/D7 (append-only) | – |

What did **not** exist before this change: any signed upload URL; any file-type/magic-byte validation; any document security state; any upload/download audit event.

**Not replaced blindly:** the working server-proxied V3 path and both legacy paths are preserved. The V3 paths (1 and 2) were hardened in place and now share one gate; the legacy paths (3 and 4) keep their own storage writes and their existing guards, and remain **unhardened** — see §8 (Step 2) and §9.

---

## 3. Security model — exact flows

### 3.1 Authorization (Step 1B), one gate

`backend/api/upload_gate.py` is the only authorization surface for document uploads. It adds no new model; it composes what is already ratified:

* `authorize_organization_upload(current_user, organization_id, repos)`
  1. authenticated principal (401);
  2. organisation principal (`is_org_member`, or internal staff oversight) else 403;
  3. the CL-42 viewer read-only rule (403 before any write);
  4. `ensure_org_access()` — tenant isolation, Processing-Entity denial (D20), internal-staff scope;
  5. returns an `UploadActor` whose `organization_id` is the tenant the bytes belong to.
* `authorize_consultant_upload(current_user, consultant_context, client_id, repos)`
  1. `require_consultant` context (else 403);
  2. `_authorized_client_org()` — grant exists, **firm owns it** (403 cross-firm), and the grant is **active** (`consultant_clients.status = 'active'`; an ended/suspended grant is denied immediately, 403);
  3. `ensure_consultant_permission(context, "upload_documents")` — the firm member's real `can_upload_documents` flag;
  4. returns an `UploadActor` whose `organization_id` is the **client's** organisation.
* Denials are audited (`document.upload_denied`, `outcome=failure`) before the HTTP error is raised.

Callers: `POST /api/v3/uploads` (ingress 1), `POST /api/v3/consultants/clients/{id}/documents` (ingress 2), and both new direct-upload endpoints.

### 3.2 Direct upload (Step 1C) — the preferred pattern

```
browser  POST /api/v3/documents/upload-url
         (or /api/v3/consultants/clients/{client_id}/documents/upload-url)
   → gate authorizes                              [§3.1]
   → filename/path safety + extension allow-list + declared size ≤ effective limit
   → server generates the object key              uploads/{org}/{YYYY}/{MM}/{DD}/{uuid}{.ext}
   → organization_files row created, status = pending_upload
   → short-lived signed upload URL + token issued (object-scoped only)
   → 201 { document_id, storage_path, upload{url,token,...}, completion{...}, resumable{supported:false} }

browser  PUT <signed_url>            → bytes land in Supabase Storage (backend never proxies them)

browser  POST /api/v3/documents/{document_id}/upload-complete
   → gate re-authorizes (and re-resolves the consultant grant)
   → row tenant must equal the authorized tenant (cross-tenant = 403)
   → status must be pending_upload (idempotent when already clean/processing)
   → completion window check (24 h) → 409 when stale
   → path must be a canonical CarbonTally key for that tenant → 409 otherwise
   → object must exist in storage → 409 otherwise
   → real stored size verified; 0/absent → quarantined 409; > limit → quarantined 413
   → security gate over the stored bytes (§4)
   → ACCEPT: status=clean, verified size recorded, audit events, then the SAME durable
             processing pipeline as the proxied path (extraction item + job; OCR prefill deferred)
   → REJECT: status=rejected (quarantined), audited, 422, never enqueued, never signed
```

What the browser never receives: the service-role key, any Supabase project/JWT credential, an unrestricted storage path, or the ability to choose the object key. Resumable/TUS is deliberately advertised as unsupported (see §8).

---

## 4. Storage model

### 4.1 Buckets and keys

| Item | Value | Authority |
|---|---|---|
| Bucket for customer documents | `documents` — private, no public access | ratified D32 (`20260823000000_d32_private_documents_storage.sql`) |
| Object key | `uploads/{client_organization_id}/{YYYY}/{MM}/{DD}/{uuid4hex}{.ext}` | generated by `services/storage_keys.build_document_storage_key` |
| Report artefacts | `report-artifacts`, unchanged (ratified B4-D5/D6/D7 model) | not touched by Step 1 |
| Consultant bucket / namespace | **none** — none was created | ratified storage decision |

Key properties, and why:

* the first segment stays `uploads` and the second stays the **client organisation id** — exactly the prefix the ratified D32 storage predicate already authorises for that organisation's active members. The new key convention therefore *preserves* the existing storage-RLS coverage instead of escaping it;
* the user file name is **not** part of the key (previously `{uuid}_{filename}`); it is preserved as `organization_files.name` (sanitised) and `metadata.original_filename` — provenance only;
* the tenant segment is validated (UUID or safe slug token) so a caller can never inject path segments through `organization_id`;
* the extension is sanitised to `[a-z0-9]{1,8}` or dropped;
* a consultant-originated object key is byte-for-byte the same shape as a customer-originated one — **no separate consultant tenancy exists**, per the ratified decision.

### 4.2 Storage-side controls (Step 1G)

| Required control | Status after Step 1 |
|---|---|
| Private buckets | Already ratified/implemented (D32) — unchanged. |
| No public document access | All *new* code paths use signed URLs only. `services/storage.py` contains no `get_public_url`. Residual legacy `get_public_url()` call sites in `routes/upload.py` (2) and `routes/organizations/files.py` (1) are listed in §8 — they are legacy, they do not affect the new flow, and the bucket is private so those URLs are non-functional. |
| Short-lived signed download URLs | Existing (`storage_signed_url`, 3600 s) — unchanged. |
| Short-lived signed upload URLs | **Implemented** (`create_signed_upload_url`); declared TTL 900 s, object-scoped, single token. |
| Backend authorization before issuing signed URLs | **Implemented** — the gate runs before signing on both initiate and download. |
| Client organisation as storage tenancy | **Implemented** — key tenant = the gate-authorized client organisation. |
| Consultant access through relationship/capability checks | **Implemented** — active grant + firm ownership + `can_upload_documents`. |
| No consultant-owned storage tenancy | **Implemented** (nothing to remove; nothing added). |
| No cross-organisation object access | **Implemented** — the row's tenant must equal the gate-authorized tenant; objects are keyed per tenant. |

### 4.3 Storage RLS vs the application authorization model — the documented gap (required by Step 1G)

The baseline/PO-evidence review established the current storage-RLS position: one predicate set (`d32_documents_*`) that authorises `uploads/{org}/…` for an organisation's **active members**, with **no consultant branch**, and no coverage of the other live prefixes (`batches/…`, `manual_review/…`, `organizations/…`, `repaired_pdfs/…`). All application I/O uses the service-role client, which bypasses storage RLS entirely.

Step 1's position on that gap, stated plainly:

1. **The application layer remains the enforcement point for consultant access.** Storage RLS cannot express a consultant grant, and Step 1 does not attempt to extend it (that would be a new storage tenancy model). Consultants reach objects only through the backend, which authorizes first and then signs a URL with the service-role client.
2. **The direct user-JWT storage path is not used by the new flow.** The browser holds only a signed, single-object token; it never holds a user JWT that could address `storage.objects` directly. Closing the remaining direct-JWT coverage/precedence questions is **not** in Step 1 (see §8).
3. **New objects are placed where the D32 predicate is already valid** (`uploads/{org}/…`), so the covered subset of objects grows rather than shrinks.
4. **Nothing here is claimed as a fix** for the uncovered legacy prefixes, the missing consultant branch, or the direct-JWT surface. Those remain open, and the PO-evidence review already records them as PO questions (its Q4/Q5/§8 items).

---

## 5. Malware scanning — exactly what is implemented

**What executes on every upload today:** the built-in `StructuralScanner` (`services/document_security.py`). It always runs, for both the proxied and the direct ingress, and its verdict is persisted on the document and in the audit trail.

| Check | Rule |
|---|---|
| Empty/truncated upload | a 0-byte object ⇒ blocker `empty_file` |
| Filename/path safety | NUL/control characters, path separators, traversal, over-length ⇒ blocker `unsafe_filename` |
| Allowed extensions | allow-list = the product's renderable/classifiable set (`pdf, jpg, jpeg, png, gif, webp, bmp, csv, xlsx, xls`) ⇒ blocker `extension_not_allowed` |
| Actual content detection (magic bytes) | `%PDF-`, JPEG, PNG, GIF, BMP, RIFF/WEBP, ZIP container (xlsx), OLE container (xls), `MZ`, ELF, Mach-O, `#!`, markup |
| Declared-vs-detected agreement | a detected family incompatible with the declared extension ⇒ blocker `content_type_mismatch`; nothing recognisable ⇒ **warning** `content_type_unverified` |
| Executable / script payloads | never accepted as evidence ⇒ blocker `executable_content`. For a text-declared file (csv) it is a warning (`executable_signature_in_text`) because the bytes are inert and a legitimate CSV whose first characters are `MZ` must not be a false positive |
| Malware test signature | the industry-standard **EICAR** string ⇒ blocker `malware_signature` |
| PDF active content | `/JavaScript`, `/JS`, `/OpenAction`, `/Launch`, `/EmbeddedFile` ⇒ warning `pdf_active_content` (recorded, never stripped) |
| Browser MIME trust | a generic or absent browser MIME is recorded (`declared_mime_generic`); the decision never rests on the browser value |

**What is NOT claimed.** No antivirus or malware engine is installed in this repository, so **no virus scan executes**. The verdict is recorded as `scanner = "structural"` with `external_scan_available = false`, and every surface says exactly that. A `CARBONTALLY_DOCUMENT_SCANNER` value that is not an installed provider logs a warning and still reports `structural` as the scanner that ran — it never fabricates a vendor result.

**Integration / configuration boundary (the remaining dependency).** An external malware scanner plugs in at one place: the `DocumentScanner` protocol consumed by `resolve_scanner()`, i.e. `scan(content, filename, declared_mime, extension) -> ScanVerdict`. Installing a vendor means (a) implementing that interface in a new module, (b) returning it from `resolve_scanner()` when configured, and (c) supplying the vendor credential through deployment configuration. No vendor, endpoint, SDK, key or vendor decision was invented or hard-coded. Deferred to Step 2 (§8).

---

## 6. Lifecycle and limits

### 6.1 Document security lifecycle

`organization_files.status` is an existing free-text `VARCHAR` with **no CHECK constraint** (initial schema), so the lifecycle needs **no migration**.

```
pending_upload ──▶ security_check_pending ──▶ clean ──▶ processing ──▶ failed
      │                      │                 ▲
      └──────────────────────┴──▶ rejected    (terminal for the gate)

uploaded   (rows written before this lifecycle existed) = legacy-accepted
```

* Permitted transitions: `STATUS_TRANSITIONS` in `services/document_security.py`.
* `is_processable()` refuses `pending_upload` and `rejected`.
* `is_downloadable()` refuses `pending_upload`, `security_check_pending` and `rejected`, while treating pre-lifecycle rows (`NULL`) as legacy-accepted so historical documents stay viewable.
* **"Only CLEAN documents enter normal processing" is enforced, not asserted:** the proxied ingress rejects *before* writing anything (no row, no object — consistent with the existing CT-FINAL-01 "no partial evidence" policy), and the direct ingress marks `rejected` and returns before the enqueue call. Both are covered by tests.
* Quarantine is a **logical** state in Step 1: the bytes remain in the client organisation's own namespace, unreachable through the application (never signed, never listed as processable). Physical isolation (a separate quarantine prefix) or deleting the object is deliberately **not** implemented: deleting customer bytes would be destructive cleanup, which Step 1 forbids.

### 6.2 Limits (Step 1J)

* **One authoritative limit**: `utils/upload_limits.py`, resolved once per request by `resolve_policy()` from the admin-configurable Upload Policy. Every ingress (proxied V3, consultant V3, and the new direct flow, at both initiate and complete) calls the same resolver.
* Ratified platform cap: **10 MB per file** (`PLATFORM_MAX_FILE_SIZE_MB`), 50 files/batch, 500 MB/batch — unchanged and not silently altered.
* Out-of-the-box effective value when nothing is configured: **6 MB per file** (`DEFAULT_MAX_FILE_SIZE_MB`), so the effective per-file limit today is **6 MB**, and an administrator may raise it to 10 MB or lower it.
* The direct flow advertises the effective limit to the client (`max_size_bytes`) and refuses a declared size above it (413) at initiation, and an actual stored size above it (413) at completion.
* Admin-configurable **subscription/capacity** rules remain a separate concern (billing plan/usage); no capacity rule was merged into the per-file safety limit.
* Oversized uploads get a clear message naming the limit; the original is **never** compressed or rewritten.

**Discrepancy still open (see §9):** the live Supabase `documents` bucket remains at a smaller storage-layer `file_size_limit` (2 MiB per the PO evidence review) because `20261024000000_ct_final_01_documents_bucket_size_limit.sql` is not applied in the live environment. Storage-layer limits cannot be raised from application code and Step 1 does not deploy. The application limit is correct and authoritative; the storage-layer cap is a deployment/execution item.


---

## 7. Tests

### 7.1 Added

`backend/tests/unit/api/test_storage_management_step1.py` — 30 tests. They use the existing in-memory conventions (`tests/unit/api/conftest.py` fixtures + `fakes.py`; no database, no storage, no network) and replace only the storage functions and the pipeline enqueue with in-memory doubles.

| Required Step 1K case | Test |
|---|---|
| 1. authorized organisation upload | `test_authorized_organization_upload_full_lifecycle` |
| 2. unauthorized organisation upload | `test_cross_tenant_upload_is_denied_before_any_write`, `test_viewer_cannot_start_an_upload` |
| 3. consultant upload for an active authorized client | `test_consultant_upload_is_scoped_to_the_client_organization` |
| 4. consultant upload after relationship termination | `test_consultant_upload_after_relationship_termination_is_denied` |
| 5. consultant upload without the required capability | `test_consultant_upload_without_the_capability_is_denied`, `test_consultant_cannot_start_an_upload_for_another_firms_client` |
| 6. cross-organisation path attempt | `test_completing_another_organizations_document_is_denied` |
| 7. arbitrary storage-path attempt | `test_arbitrary_storage_path_and_disallowed_extensions_are_refused`, `test_storage_key_rejects_a_tenant_token_that_could_inject_a_path`, `test_filename_safety_and_extension_sanitisation`, `test_storage_key_is_server_generated_and_tenant_scoped` |
| 8. oversized file | `test_oversized_upload_is_refused_before_any_write`, `test_stored_object_larger_than_the_limit_is_quarantined`, `test_zero_byte_declared_upload_is_refused` |
| 9. incorrect/mismatched content type | `test_mismatched_content_type_is_quarantined_at_completion`, `test_security_gate_rejects_executables_mismatches_and_the_eicar_signature`, `test_security_gate_tolerates_unrecognised_bytes_but_never_trusts_the_mime` |
| 10. malicious/failed security-scan lifecycle | `test_malware_signature_upload_is_rejected_and_never_processed`, `test_unconfigured_external_scanner_never_claims_a_malware_scan` |
| 11. clean document lifecycle | `test_authorized_organization_upload_full_lifecycle`, `test_lifecycle_status_rules_fail_closed`, `test_ratified_cap_is_unchanged_and_single_sourced` |
| 12. signed upload URL expiration | `test_expired_upload_authorisation_is_refused`, `test_completion_without_the_stored_object_is_refused` |
| 13. signed download authorization | `test_signed_download_requires_authorization_and_is_audited` |
| 14. consultant provenance preservation | `test_consultant_upload_is_scoped_to_the_client_organization`, `test_upload_audit_entries_carry_provenance_and_no_credential` |
| 15. consultant-managed → direct customer, no storage movement | `test_consultant_provenance_survives_client_conversion_without_moving_bytes` |
| 16. original document remains unchanged | `test_the_original_document_is_never_rewritten` |
| 17. audit event creation | `test_upload_audit_entries_carry_provenance_and_no_credential`, `test_signed_download_requires_authorization_and_is_audited`, `test_server_proxied_upload_uses_the_same_gate_and_security_check` |
| (extra) shared gate on the legacy proxied ingress | `test_server_proxied_upload_uses_the_same_gate_and_security_check` |

### 7.2 Changed

`backend/tests/unit/api/fakes.py` — `MemoryFiles` now mirrors the extended repository contract: `status` on `create`, `update_status(id, status, size_bytes=None)`, mapping-aware `update_metadata`, and `uploaded_at`. No existing test behaviour was altered.

### 7.3 Results

| Suite | Command | Result |
|---|---|---|
| Step 1 suite | `.venv/bin/python -m pytest tests/unit/api/test_storage_management_step1.py -q` | **30 passed** |
| Pre-existing upload/storage/consultant suites | `pytest tests/unit/api/test_ct_final_01_upload_limits.py test_storage_security.py test_v3_phase_c_regressions.py test_v3_consultants.py test_step2_stabilization_enqueue_visibility.py test_legacy_upload_idor.py test_legacy_manual_review_adapter.py test_document_content_type.py test_v3_routes_exposed.py -q` | **123 passed** |
| Whole unit suite | `.venv/bin/python -m pytest tests/unit -q` | see §7.4 |

### 7.4 Whole-unit-suite result

Command: `.venv/bin/python -m pytest tests/unit -q --no-header --tb=no -p no:cacheprovider`

Result: **exit code 1 — exactly 8 failures**, all of them pre-existing and outside the surface this change touches:

| Failing test | Area | Cause (observed) |
|---|---|---|
| `tests/unit/api/test_v3_discovery.py::TestDiscoveryRequests::test_create_request_as_admin` | Discovery API | pre-existing uncommitted work in `api/v3_discovery.py` (untouched by Step 1) |
| `tests/unit/data/test_d17_provider_ownership_migration_revision.py::test_migration_ordering_is_unchanged` | migration revision ordering | pre-existing migration files in the tree |
| `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | migration revision ordering | pre-existing migration files in the tree |
| `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | migration revision ordering | pre-existing migration files in the tree |
| `tests/unit/data/test_p17_migrations.py::test_p17_does_not_reuse_or_edit_a_historical_timestamp` | migration timestamp hygiene | pre-existing migration files in the tree |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice` | extraction suggestions | date normalisation (`'2026-01-15' == '15/01/2026'`) in pre-existing engine work |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved` | extraction suggestions | same engine area (`extraction_evidence` key present) |
| `tests/unit/engines/test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage` | extraction suggestions | same engine area |

&#42; Step 1 added **no** migration and changed **no** extraction/discovery code, so none of these can be attributed to it. The same 8 failures were observed on two independent full-suite runs in this session. This pytest environment does not print a "N passed" summary line (verified: the output ends at the failure list), so the passed count is not available; the targeted suites below cover the whole touched surface and pass.

Targeted verification (paths Step 1 actually touched):

| Command | Result |
|---|---|
| `pytest tests/unit/api/test_storage_management_step1.py -q` | **30 passed** |
| `pytest tests/unit/api/test_ct_final_01_upload_limits.py tests/unit/api/test_storage_security.py tests/unit/api/test_v3_phase_c_regressions.py tests/unit/api/test_v3_consultants.py tests/unit/api/test_step2_stabilization_enqueue_visibility.py tests/unit/api/test_legacy_upload_idor.py tests/unit/api/test_legacy_manual_review_adapter.py tests/unit/api/test_document_content_type.py tests/unit/api/test_v3_routes_exposed.py -q` | **123 passed** |
| `.venv/bin/python -c "import api.router"` | imports cleanly; the four new routes are registered |
| `.venv/bin/python -m compileall -q api services data tests/unit/api` | no syntax errors |



---

## 8. Not implemented — deliberately deferred (Step 2 or later governance)

| Deferred item | Why it is not in Step 1 |
|---|---|
| **External malware/virus scanning vendor integration** | No approved scanner exists in the repository. Step 1 provides the lifecycle, the interface and the configuration boundary only, and never claims a scan that did not run. |
| **Resumable / TUS uploads** | The ratified per-file cap is 10 MiB, which a signed PUT covers; a TUS session would require exposing a storage-level credential (project key or user JWT) to the browser. The API response states `resumable: {supported: false, reason: …}` rather than implying it. |
| **Frontend / browser wiring of the new endpoints** | Step 1 delivers the backend contract (`upload-url`, `upload-complete`, for both the organisation and consultant surfaces). No UI was changed, so the existing proxied ingress remains the path the current UI uses. |
| **Hardening the two legacy ingresses** (`POST /api/upload`, `POST /api/organizations/{org}/files/upload`) | They keep their own storage writes and their existing guards; they were **not** rewired onto the signed-upload flow. Their residual `get_public_url()` call sites (3 in total, non-functional against a private bucket) are also untouched. |
| **Physical quarantine isolation and object deletion for rejected uploads** | Deleting or relocating customer bytes is destructive cleanup, which Step 1 forbids. Quarantine is enforced logically (never enqueued, never signed). |
| **Storage retention / destruction policy and lifecycle automation** | Explicit Step 1 stop condition. |
| **Consultant handover workflow** and per-client capability mechanism | Explicit Step 1 stop condition; the server enforces the existing active-grant + capability rules only. |
| **Billing/subscription redesign or any second entitlement system** | Explicit Step 1 stop condition. No entitlement code was added or changed. |
| **Report-artefact storage changes** | Ratified separately; untouched. |
| **Storage-RLS extension (consultant branch, prefix coverage, direct user-JWT path)** | Would require a new storage-tenancy model; §4.3 documents the gap instead. |
| **Bounded range-read for the completion probe** | The completion step reads the stored object through the existing download helper and slices a 256 KiB prefix for the gate. With the 10 MiB cap this is bounded and acceptable; a true range read is a Step 2 optimisation. |
| **Wiring the direct-upload completion into OCR prefill** | The direct flow passes `content=None`, so the OCR prefill is recorded as `deferred` and the pipeline's ingest stage reads the object from storage. No partial-text artefact is persisted. |
| **Migration application / deployment** | Not authorised. |

---

## 9. Risks and blockers

**Real blockers (none of which block Step 1's own completion):**

1. **Storage-layer file-size cap in the live environment.** The live `documents` bucket remains at its previous `file_size_limit` (2 MiB per the PO evidence review) because `20261024000000_ct_final_01_documents_bucket_size_limit.sql` is not applied there. Application-level enforcement is correct (6 MB effective / 10 MB ratified cap), but any direct upload between the live storage-layer cap and the application limit will be refused by Supabase Storage. Applied by deployment, not by code.
2. **No malware scanner is installed.** Until a provider is implemented and configured, the platform's security gate is structural only. This is disclosed in the verdict, the API response and this report — not hidden.
3. **Frontend adoption.** The new endpoints are unused until the browser calls them, so the security benefit of the direct flow is not realised end-to-end yet.

**Risks to be aware of (not blockers):**

* The direct flow **creates the document row before the object exists** (`pending_upload`). An abandoned upload leaves a `pending_upload` row and no object; it is not downloadable, not processable, and becomes un-completable after the 24 h window. A Step 2 retention/cleanup rule (governance-owned) should reap those rows.
* A security-**rejected** direct upload leaves its bytes in the client's namespace (logically quarantined). Step 2 must decide the physical disposition with the Product Owner.
* The legacy ingresses remain unhardened, so a legacy caller can still store a document that never passes the security gate. The gate governs the V3 canonical pipeline (both V3 ingresses) and the new direct flow only.
* Two ingestion shapes now exist for one pipeline: the proxied ingress still transfers bytes through the backend by design (a single request/response with the file), while the direct ingress does not. The shared `enqueue_document_processing()` keeps the *downstream* behaviour identical.

---

## 10. Verification status

* Step 1 scope only: **complete**. Every item in Step 1A–1L is either implemented and verified, or explicitly listed as deferred in §8 with the reason.
* No production deployment, no migration application, no production data mutation, no destructive cleanup, no commit and no push.
* Nothing was implemented from the Step 2 / stop-condition list.

**STORAGE MANAGEMENT STEP 1 — CLOSED** (verified together with Step 2; closure record in
`CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md` §20 and
`CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.4). Production deployment **NOT AUTHORIZED**.
