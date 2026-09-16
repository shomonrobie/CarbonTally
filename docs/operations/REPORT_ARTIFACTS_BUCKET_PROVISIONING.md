# `report-artifacts` bucket — operational provisioning (D-11)

**Decision (PO, P8-FINALIZATION-IMPLEMENT-001):** use **operational
provisioning**. No migration is created solely to create the bucket.

**Current state:** the bucket is **mandated** by the ratified B4 decision and by
the schema itself, but **it has not been created in any environment reachable from
the build checkout** (only `documents` exists — private). Application code does not
create the bucket: the B4 migration states "No storage object is created by this
migration", and no `create_bucket` call exists anywhere in `backend/`.

## 1. Required properties (non-negotiable)

| Property | Value / rule |
|---|---|
| Bucket name | `report-artifacts` — enforced by `CHECK (storage_bucket = 'report-artifacts')` and by the single constant `ARTEFACT_BUCKET` |
| Privacy | **private** (`public = false`). No public URL path exists in the adapter (`services/report_artefact_storage.py` uses signed URLs only) |
| Object key | derived from the row: `{organization_id}/{report_id}/{report_version_id}.pdf` |
| Integrity | SHA-256 lowercase hex, recorded in `report_version_artifacts.content_sha256`; `byte_size > 0` |
| Immutability | one artefact row per finalised version (`UNIQUE (report_version_id)`); upload uses `upsert=false` — a frozen artefact is never overwritten |
| Access | short-lived signed URLs (TTL 300 s) issued **after** authorization; service-role only |

## 2. Provisioning procedure (per environment)

Repeat for **each** environment (local QA/clone, staging, production):

1. **Supabase dashboard** → Storage → *New bucket*
   * name: `report-artifacts` (exact — no prefix/suffix)
   * **Public bucket: OFF**
   * file size limit: at least the largest expected report PDF (reports are
     generated as PDFs; keep the platform default unless a limit is required)
2. **Or Supabase CLI** (project linked, authenticated):
   `supabase storage create report-artifacts --private`
3. **No storage policies are required for the service role path.** If a
   policy-managed path is ever added, it must not grant `anon` any access and must
   not allow public read.

## 3. Verification after provisioning (evidence to capture)

```sql
-- bucket exists and is private
select name, public from storage.buckets where name = 'report-artifacts';
-- expected: report-artifacts | false
```

Application-level verification (bounded, read-only preflight):

```bash
# adapter preflight (no writes) — reports whether the bucket is reachable
python -c "from services.report_artefact_storage import get_report_artefact_storage as g; print(g().bucket_exists())"
```

Then one **end-to-end finalisation** in a disposable environment: finalise a
draft report version and assert (a) upload succeeded, (b) the
`report_version_artifacts` row carries the derived key + SHA-256, (c) the
signed-URL download returns the same bytes. The unit/runtime suites use the
in-memory adapter, so this e2e step is the only proof that the real storage path
works.

## 4. Status

| Item | State |
|---|---|
| Procedure documented | **yes** (this file) |
| Bucket created locally / in staging / in production | **NO — not performed**; no provider credentials were used and no bucket was created |
| Application preflight available | `SupabaseReportArtefactStorage.bucket_exists()` (read-only, list-based) |
| Remaining operator action | run §2 in each environment and capture §3 evidence; production is subject to the D-17 authorisation gate |
