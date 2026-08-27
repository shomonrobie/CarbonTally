---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md, CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md
---

# CarbonTally V3 — Legacy Capability Reimplementation Report

## 1. Executive Summary

Thirteen legacy capabilities were reimplemented cleanly under the V3 layered
architecture (repositories → thin API routers → composition root), following the
existing v2.1 conventions (`data.base.AbstractRepository`, `api.dependencies`
`RepositoryBundle`, `auth.py` guards). No legacy code was deleted, no database /
schema / RLS / migration was modified, and the new surface is mounted on the
single V3 router (and therefore on the `main.py` composition root).

## 2. Scope

Reimplemented capabilities: upload, documents, batches, organizations, members,
assets, facilities, exports, review, assignment, SLA, verification, notifications.

## 3. What was built

**Domain models** — `domain/operations.py`: `MemberRecord`, `FacilityDetail`,
`AssetDetail`, `OrganizationFile`, `UploadBatch`, `ReviewItem`, `QueueSettings`,
`Notification`, `Verification` (immutable dataclasses mirroring the RC2 tables).

**Repositories** (`data/`, all asyncpg over the service-role pool):
- `tenant.py` — `TenantRepository` (member/facility/asset create/update/remove).
- `organization_files.py` — `OrganizationFilesRepository` (upload/document records).
- `upload_batches.py` — `UploadBatchesRepository`.
- `review_queue.py` — `ReviewQueueRepository` (manual_review_queue lifecycle).
- `queue_settings.py` — `QueueSettingsRepository` (defaults + upsert).
- `verifications.py` — `VerificationsRepository` (customer_documents decisions).
- `notifications.py` — `NotificationsRepository`.
- `exports.py` — `ExportsRepository` (read-only emissions/documents queries).

Existing `data/organizations.py` (`OrganizationsRepository`) and
`data/documents.py` (`DocumentsRepository`) are reused for the read side.

**API routers** (`api/`, thin, inline typed contracts, `auth.py` guards):
- `v3_organizations.py` → `/api/v3/organizations/*` (org, members, facilities, assets).
- `v3_documents.py` → `/api/v3/uploads`, `/api/v3/documents`, `/api/v3/batches`.
- `v3_review.py` → `/api/v3/admin/review-queue`, `/api/v3/admin/sla/settings`.
- `v3_verifications.py` → `/api/v3/verifications/*` (approve/reject/correct).
- `v3_notifications.py` → `/api/v3/notifications`.
- `v3_exports.py` → `/api/v3/exports/emissions.csv|json`, `/documents.csv`.

**Wiring**: `data/__init__.py` exports the new repositories;
`api/dependencies.py` extends `RepositoryBundle`; `api/router.py` includes the
six new routers (so they are served by `main.py` and by `main_v2.py`).

**Tests**: `tests/unit/api/test_v3_legacy_reimplementation.py` asserts the new
routes are registered; existing Phase-1 tests continue to cover the engine
endpoints and the composition root.

## 4. Files created / changed

Created: `domain/operations.py`, `data/tenant.py`, `data/organization_files.py`,
`data/upload_batches.py`, `data/review_queue.py`, `data/queue_settings.py`,
`data/verifications.py`, `data/notifications.py`, `data/exports.py`,
`api/v3_organizations.py`, `api/v3_documents.py`, `api/v3_review.py`,
`api/v3_verifications.py`, `api/v3_notifications.py`, `api/v3_exports.py`,
`tests/unit/api/test_v3_legacy_reimplementation.py`, and this report.

Changed: `data/__init__.py`, `api/dependencies.py`, `api/router.py`.

## 5. Capability → endpoint mapping

| Capability | V3 endpoint(s) | Auth |
|---|---|---|
| organizations | GET /api/v3/organizations/{org_id} | org member |
| members | GET/POST /api/v3/organizations/{org_id}/members; PUT/DELETE /api/v3/organizations/members/{id} | member / org admin |
| facilities | GET/POST /api/v3/organizations/{org_id}/facilities; DELETE /facilities/{id} | member / org admin |
| assets | GET/POST /api/v3/organizations/{org_id}/assets; DELETE /assets/{id} | member / org admin |
| upload | POST /api/v3/uploads | org member |
| documents | GET /api/v3/documents; GET /documents/{id} | org member |
| batches | POST /api/v3/batches; GET /batches; GET /batches/{id} | org member |
| review | GET /api/v3/admin/review-queue; GET /review-queue/{id} | admin |
| assignment | POST /api/v3/admin/review-queue/{id}/assign | admin |
| SLA | GET/PUT /api/v3/admin/sla/settings | admin |
| verification | GET /api/v3/verifications/pending; POST /{id}/approve|reject|correct | org member |
| notifications | GET /api/v3/notifications; POST /{id}/read; POST /read-all | auth |
| exports | GET /api/v3/exports/emissions.csv|json, /documents.csv | org member |

## 6. Design decisions

1. Clean reimplementation, not a wrapper: every capability has a typed
   repository and a thin router; no legacy module is imported by the new code.
2. Upload writes to Supabase Storage (`infra.supabase.get_service_client`) and
   records an `organization_files` row — same storage contract as the legacy
   surface, but through the repository layer.
3. Verification is stored on `customer_documents` (status / verified_by /
   verified_at / metadata) — matching the current schema; a dedicated
   verification table can be introduced later without changing this surface.
4. Notifications repository uses only the columns confirmed to exist
   (`id, user_id, is_read, priority, created_at`).
5. Exports are computed read-only from `emissions_logs` and `organization_files`;
   no export-history table is assumed.
6. RepositoryBundle and router wiring follow the existing v2.1 composition-root
   pattern exactly, so the new surface is served by both `main.py` and
   `main_v2.py`.

## 7. Verification status

**Executed (static):** every new/modified file was created and re-read for
syntax and internal consistency (imports resolve within the package graph,
abstract-repository methods implemented, guards imported from `auth.py`,
routers included in `api/router.py`, repos wired into `RepositoryBundle`).

**Not executed (environmental):** `pytest` / `uvicorn` / live DB checks could not
run in this session because the shell tool is wedged on a hung `docker exec`
from a previous session. This is an environment limitation, not a code defect.
The tests and commands in §8 must be run from a healthy shell/CI before these
routes are considered verified against the live database.

## 8. Commands to run

```bash
cd backend
python -m pip install -r requirements.txt
python -m py_compile main.py api/v3_organizations.py api/v3_documents.py \
    api/v3_review.py api/v3_verifications.py api/v3_notifications.py \
    api/v3_exports.py data/tenant.py data/organization_files.py \
    data/upload_batches.py data/review_queue.py data/queue_settings.py \
    data/verifications.py data/notifications.py data/exports.py domain/operations.py
python -m pytest tests/unit/api/test_v3_routes_exposed.py -q
python -m pytest tests/unit/api/test_composition_root.py -q
python -m pytest tests/unit/api/test_v3_legacy_reimplementation.py -q
python -m pytest tests/unit -q
uvicorn main:app --host 0.0.0.0 --port 8000   # then curl /openapi.json and the new routes
```

## 9. Limitations & next steps

- Runtime/DB verification pending (see §7). The repositories assume the RC2
  column shapes used by the legacy routes; any drift in a specific table will
  surface in integration tests.
- Upload does not yet trigger the extraction/review pipeline (a
  `manual_review_queue` row can be created by the review surface); wiring
  upload → processing → review is the next engine-integration step.
- Verification currently updates `customer_documents`; a dedicated
  verification/result-chain contract (extracted → mapped → factor →
  calculation → result) is the follow-on.
- Exports are computed on demand; a queued export job + export-history table is
  a later async-work item.
- Notifications is in-app only; email dispatch (Resend) is a separate service.

## 10. Risks

1. Untested SQL against live tables — mitigated by integration tests (needs the
   local Supabase stack) before use.
2. New repositories increase the per-request `RepositoryBundle` construction
   cost slightly (one pool, many lightweight repos) — acceptable.
3. `queue_settings` upsert relies on a stable primary key (`id`); confirm the
   table has one in the RC2 schema.
4. Upload storage failure path returns 500 with a safe message; the file is not
   orphaned in `organization_files` because the record is written after upload.

