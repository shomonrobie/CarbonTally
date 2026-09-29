-- ============================================================================
-- CarbonTally CT-FINAL-01 — upload limits: pin the `documents` bucket size limit
-- File: 20261024000000_ct_final_01_documents_bucket_size_limit.sql
--
-- RATIFIED PRODUCTION SCOPE (CT-FINAL-01, upload limits):
--   10 MB per file · 50 files per batch · 500 MB per batch, enforced SERVER-SIDE.
--
-- The application now enforces those limits in code
-- (`backend/utils/upload_limits.py`, applied at every document ingress). This
-- migration aligns the STORAGE layer with the same number so a client that
-- bypasses the application (direct-to-storage upload with a user JWT) cannot
-- exceed the ratified per-file limit:
--
--   * `storage.buckets.file_size_limit` for `documents` is set to 10485760 bytes
--     (10 MiB) when it is currently unset OR larger than the ratified cap.
--     A *smaller* existing limit is never raised (configuration may only
--     tighten) — the statement is therefore a no-op once aligned.
--   * `documents` is re-asserted PRIVATE (`public = FALSE`), which is already
--     the D32 end state; the assertion is idempotent and makes this file safe to
--     re-run.
--
-- WHAT THIS DOES NOT TOUCH:
--   * `report-artifacts` (internally generated report output — not a user upload
--     ingress) — unchanged;
--   * storage RLS policies, grants, object data, or any application table;
--   * no object is moved, rewritten or deleted.
--
-- PORTABILITY: the file can only be meaningful where the Supabase storage layer
-- is provisioned. Where `storage.buckets` is absent (a bare PostgreSQL instance
-- used for schema-only work) the migration is a deliberate NO-OP instead of a
-- failure, so it cannot break a storage-less environment. Where the layer IS
-- present the final state is asserted and the migration fails loudly if the
-- limit is not in force.
--
-- IDEMPOTENT: re-running is a no-op (bounded UPDATE + guarded assertion).
-- Nothing is deployed by this file: no push, no migrate, no production change.
-- ============================================================================

DO $ct_final_01_upload_limits$
DECLARE
    ratified_limit constant bigint := 10485760;  -- 10 MiB, mirrors upload_limits.py
    current_limit bigint;
    current_public boolean;
BEGIN
    IF to_regclass('storage.buckets') IS NULL THEN
        RAISE NOTICE
            'CT-FINAL-01: storage layer not provisioned in this database — '
            'bucket-level size limit not applicable (application-level limits '
            'remain in force).';
        RETURN;
    END IF;

    SELECT file_size_limit, public
      INTO current_limit, current_public
      FROM storage.buckets
     WHERE name = 'documents';

    IF NOT FOUND THEN
        RAISE NOTICE
            'CT-FINAL-01: bucket "documents" is absent in this database — '
            'nothing to align (provision storage before applying the chain).';
        RETURN;
    END IF;

    -- Tighten only: never raise a smaller, deliberately configured limit.
    UPDATE storage.buckets
       SET file_size_limit = ratified_limit
     WHERE name = 'documents'
       AND (file_size_limit IS NULL OR file_size_limit > ratified_limit);

    -- Private remains the required end state (D32) — idempotent re-assertion.
    UPDATE storage.buckets
       SET public = FALSE
     WHERE name = 'documents'
       AND public = TRUE;

    -- Fail-closed verification of the resulting state.
    SELECT file_size_limit, public
      INTO current_limit, current_public
      FROM storage.buckets
     WHERE name = 'documents';

    IF current_limit IS NULL OR current_limit > ratified_limit THEN
        RAISE EXCEPTION
            'CT-FINAL-01 precondition failed: documents.file_size_limit = % '
            '(expected <= %)', current_limit, ratified_limit;
    END IF;

    IF current_public IS TRUE THEN
        RAISE EXCEPTION
            'CT-FINAL-01 precondition failed: the documents bucket is public';
    END IF;

    RAISE NOTICE
        'CT-FINAL-01: documents bucket aligned — file_size_limit = %, public = %',
        current_limit, current_public;
END
$ct_final_01_upload_limits$;
