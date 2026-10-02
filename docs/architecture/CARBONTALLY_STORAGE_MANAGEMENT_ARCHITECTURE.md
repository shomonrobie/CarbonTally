# CarbonTally — Storage Management Architecture

**Document ID:** CT-STORAGE-MANAGEMENT-ARCH-20260930-001
**Repository:** `ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Base HEAD:** `cabdca8380415e73a25cf23eb393d0b15c0af391`
**Date:** 2026-09-30
**Status:** describes the implemented end state after Storage Management Step 1 + Step 2 —
**STORAGE MANAGEMENT STEPS 1 + 2: CLOSED** (implementation complete; independent verification
complete with non-blocking observations preserved; no blocking defects; deployment dependencies
separate from implementation closure). Production deployment **NOT AUTHORIZED**. Closure record:
`CARBONTALLY_STORAGE_MANAGEMENT_STEP2_IMPLEMENTATION_20260930.md` §20;
`CARBONTALLY_FINAL_PRODUCT_DECISION_REGISTER.md` §41.4.
**Authority:** this document describes the implementation; it does not create product policy. Where a decision was not ratified, it is listed under §Known limitations as an open item.

---

## 1. Buckets

| Bucket | Public | Contents | Key model |
|---|---|---|---|
| `documents` | **private** | customer- and consultant-uploaded documents, plus derived artefacts | `uploads/{organization_id}/…` (see §2) |
| `report-artifacts` | **private** | frozen report PDFs (one per finalised report version, append-only) | `{organization_id}/{report_id}/{report_version_id}.pdf` |

There is no third bucket and no consultant-owned bucket. Bucket-level protections in force:

* `documents` is private (D32) and its four storage-RLS policies are org-scoped (§4);
* both buckets are addressed only through short-lived signed URLs issued by the backend;
* the `documents` per-file size limit is pinned to the ratified 10 MiB cap by
  `20261025000000_ct_step2_documents_bucket_size_alignment.sql` (prepared; the live environment may still hold a lower value until it is applied — §10).

## 2. Object-key model

| Kind | Layout |
|---|---|
| Document (canonical) | `uploads/{organization_id}/{YYYY}/{MM}/{DD}/{uuid4_hex}{.ext}` |
| Derived artefact | `uploads/{organization_id}/derived/{uuid4_hex}{.ext}` |
| Report artefact | `{organization_id}/{report_id}/{report_version_id}.pdf` (bucket `report-artifacts`) |

Rules:

* keys are **generated server-side** (`services.storage_keys`); a client-supplied path is never accepted;
* the tenant segment must be a UUID (or a safe single-segment token) — a caller can never inject a path segment;
* the user's file name is provenance only (`metadata.original_filename`) and never determines path identity;
* the derived namespace is deliberately distinct so a derived artefact can never be mistaken for the customer's original evidence.

## 3. Tenancy

* **The client organisation is the storage tenant anchor.** Every document object lives under `uploads/{client_organization_id}/…`.
* A consultant upload is written into the **client's** namespace; the consultant firm never appears in a key.
* No clone, copy, export, move or re-import is performed when a consultant relationship changes — only authorization changes.

## 4. Authorization

```text
authenticated actor
        │
        ├── organisation member ──► require_org_member + ensure_org_access
        │                            (+ CL-42 viewer read-only denial, PE denial)
        ├── consultant ───────────► require_consultant
        │                            + ACTIVE consultant_clients grant (D15)
        │                            + firm ownership
        │                            + can_upload_documents capability
        └── internal staff ───────► operational scope rules
        ▼
   api.upload_gate  (the single authoritative gate — every ingress)
```

**What storage RLS protects:** the D32 policies on `storage.objects` grant `authenticated` access only when `bucket_id = 'documents'`, `foldername(name)[1] = 'uploads'` and `foldername(name)[2]::uuid` is one of the caller's active `organization_members`. This defends any *direct user-JWT* storage access.

**What the backend protects:** identity, organisation/consultant scope, capability, entitlement, upload policy and the document security lifecycle.

**Residual RLS limitation:** Storage RLS does not model the document lifecycle state, so a user-JWT storage read of a quarantined object would not be blocked by RLS alone. The application gate is the enforcement point and no frontend path uses direct user-JWT storage access. (Recorded, not changed.)

## 5. Upload flow (browser → backend → Storage)

```text
1. browser  ──POST /api/v3/documents/upload-url (metadata only)──►  backend
             or /api/v3/consultants/clients/{client_id}/documents/upload-url
2. backend  : upload gate → tenant resolution → capability → upload policy
              → server-generated key → organization_files row (`pending_upload`)
              → short-lived object-scoped signed upload URL
3. browser  ──PUT bytes──►  private Supabase Storage (uploads/{org}/…)
4. browser  ──POST …/upload-complete──►  backend
5. backend  : re-authorize → verify tenant prefix → verify the object exists and its real size
              → read the object back once (bounded by the effective limit)
              → security gate (structural always; external when installed/configured)
              → `clean` + audit + enqueue into the existing pipeline  (or `rejected`)
```

The browser never receives a service-role key, a project secret or unrestricted storage credentials. Resumable (TUS) uploads are refused with a stated reason.

## 6. Download flow

```text
authenticated actor
   → organization / consultant authorization (the same gate)
   → document belongs to the authorized client organisation
   → the lifecycle/security state permits reading (not pending/rejected/expired)
   → short-lived signed URL (3600 s) returned to the caller
```

Signed URLs are never persisted (not on the row, not in audit, not in `manual_review_queue`).

## 7. Security scanning

| Layer | What it does | When |
|---|---|---|
| Structural validation | extension allow-list, extension↔declared-type agreement, magic bytes, filename/path safety, empty/truncated detection, EICAR test signature, PDF active-content reporting | **always**, on every ingress |
| External malware scan | optional provider behind the `DocumentScanner` protocol | only when a provider is registered **and** configured |

| Variable | Meaning |
|---|---|
| `CARBONTALLY_DOCUMENT_SCANNER` | provider id (empty / `structural` = built-in only) |
| `CARBONTALLY_DOCUMENT_SCANNER_REQUIRED` | `true` ⇒ an external verdict is a precondition for acceptance |

Scanner states: `clean` · `malware` · `structural_rejection` · `scanner_unavailable` · `scanner_error`.
**Fail-closed:** `scanner_unavailable` and `scanner_error` quarantine the document; they are never reported as clean and never enter processing. `virus_scanned` is true only when an external provider actually returned a verdict.

## 8. Processing

A document enters the **existing** durable pipeline only after the gate accepts it:

```text
clean ──► extraction batch/item ("Uploads") ──► document_processing_queue job
      ──► ingest → extract → map → validate → calculate → review
      ──► OCR prefill recorded on organization_files.metadata
```

The direct flow hands the pipeline the verified bytes it read at completion, so it has identical page-count/OCR semantics to a server-proxied upload. Enqueue failures never fail the upload; the outcome is recorded on the document row.

## 9. Lifecycle

```text
pending_upload ──► security_check_pending ──► clean ──► processing ──► failed
      ├──► rejected          (quarantined: not processable, not downloadable)
      └──► upload_expired    (abandoned: terminal, not processable, not downloadable)
```

`is_processable()` and `is_downloadable()` are the single fail-closed predicates used by the API surfaces.

## 10. Audit

Significant document events are appended to the existing audit ledger (`api.upload_gate.record_document_event`), best-effort so an audit outage never fails an upload:

`document.upload_initiated` · `document.upload_completed` · `document.upload_denied` · `document.upload_authorisation_expired` · `document.cleanup` · `document.security_scan_started` · `document.security_scan_completed` · `document.security_scan_unavailable` · `document.security_rejected` · `document.accepted` · `document.signed_url_issued` · `document.download` · `document.deleted` · `document.derived_artefact_created`

Never persisted: signed URLs, access tokens, service-role credentials, provider secrets. Audit payloads carry identifiers, provenance, verdict metadata and lifetimes only.

## 11. Consultant model

* the **client organisation owns the storage** (objects, ids, provenance);
* the consultant is a **delegated operator**, authorized by an ACTIVE `consultant_clients` grant plus the `can_upload_documents` capability;
* there is **no consultant storage tenancy** and no consultant bucket;
* provenance (firm id, membership role, uploader, timestamps, `consultant_originated`) lives in application metadata and audit;
* when the relationship ends: bytes stay, provenance stays, consultant access ends, nothing is moved;
* when the client becomes a direct CarbonTally customer: same organisation, same objects, same document ids.

## 12. Commercial model

* Consultants are direct CarbonTally customers; their subscription covers their managed clients; CarbonTally Admin configures capacity through plans.
* Storage consumption is metered per organisation through the **existing** `billing_storage_usage` snapshot (`BillingService.meter_storage`), refreshed after an accepted upload; the included allowance is `billing_plans.included_storage_bytes` (admin-configurable).
* Over-allowance storage is **metered and billable** (`additional_bytes`), not an upload block: refusing uploads on capacity would be a new commercial policy and was not introduced.
* No parallel entitlement system exists.

## 13. Retention

| Category | Behaviour |
|---|---|
| Customer documents | soft-expire (`deleted_at`) only when `system_settings.document_retention_days` is configured; `None` ⇒ nothing purged |
| Abandoned upload authorisations | reaped to `upload_expired` after the existing 24 h completion window (idempotent, non-destructive, audited) |
| Rejected (quarantined) objects | **no physical deletion** — no ratified destruction rule exists |
| Orphaned objects | **no physical deletion** — no ratified semantics exist |
| Audit / evidence tables | never purged (security invariant) |

## 14. Known limitations (explicitly not implemented)

| Limitation | Requires |
|---|---|
| No external malware scanner is installed | an approved provider + its adapter registration + `CARBONTALLY_DOCUMENT_SCANNER[_REQUIRED]` configuration |
| The live `documents` bucket may still hold a per-file limit below the ratified cap | applying `20261025000000_ct_step2_documents_bucket_size_alignment.sql` |
| The `report-artifacts` bucket is provisioned operationally (no migration creates it) | infrastructure provisioning; `bucket_exists()` is the application preflight |
| Physical destruction of rejected/orphaned objects | an explicit Product Owner retention/destruction decision |
| Per-consultant managed-client capacity expansion | out of scope; the existing plan/subscription model governs it |
| Derived artefacts are not registered as document rows | would be new record semantics; the repair utility returns provenance instead |
| The legacy `/api/organizations/files/bulk` ingress still uses the legacy `organizations/{org}/…` key helper | a later, bounded migration (it is not in the current frontend upload path) |
| `PDFRepairTool` / `PDFIngestionPortal` call `/repair-pdf` (not `/api/repair-pdf`) | a frontend routing fix (out of Step 2 scope; the route itself is hardened) |
| Storage-layer lifecycle (auto-expiry) rules are not configured | an explicit retention decision plus provider configuration |
| The completion read is a full bounded object download | a true range read (only an optimisation at the 10 MiB cap) |
