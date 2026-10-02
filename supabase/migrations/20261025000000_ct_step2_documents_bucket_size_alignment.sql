-- ============================================================================
-- CarbonTally Storage Management Step 2I — align the `documents` bucket size
-- limit with the ratified per-file cap.
-- File: 20261025000000_ct_step2_documents_bucket_size_alignment.sql
--
-- WHY THIS FILE EXISTS (Step 2I):
--   The ratified platform maximum is 10 MiB per file
--   (`backend/utils/upload_limits.py` PLATFORM_MAX_FILE_SIZE_MB = 10; the
--   out-of-the-box effective default is 6 MB).  The PO evidence review recorded
--   the LIVE `documents` bucket at 2 MiB, and
--   `20261024000000_ct_final_01_documents_bucket_size_limit.sql` could not
--   correct that because it deliberately only TIGHTENS
--   (`file_size_limit > ratified_limit`).  The result was a storage layer that
--   silently refused valid uploads the application would accept.
--
--   This migration makes the storage layer equal the ratified cap in EITHER
--   direction, so the application's supported per-file limit is never silently
--   capped underneath it:
--
--     * `storage.buckets.file_size_limit` for `documents` := 10485760 bytes
--       (10 MiB) whenever it is unset or different;
--     * `documents` is re-asserted PRIVATE (`public = FALSE`, the D32 end state);
--     * the resulting state is verified and the migration FAILS LOUDLY if the
--       limit is not exactly the ratified value.
--
-- WHAT THIS DOES NOT CHANGE:
--   * the RATIFIED PRODUCT CAP itself (still 10 MB per file) — no product
--     decision is altered, and no per-file/plan capacity is introduced;
--   * `report-artifacts` or any other bucket — `documents` only;
--   * storage RLS policies, grants, or any object (no object is moved,
--     rewritten or deleted);
--   * any application table.
--
-- PORTABILITY: where the Supabase storage layer is absent (a bare PostgreSQL
-- instance used for schema-only work) the file is a deliberate NO-OP instead of
-- a failure.
--
-- IDEMPOTENT: re-running is a bounded no-op (the guarded UPDATE and the
-- assertion converge on the same value).
--
-- DEPLOYMENT BOUNDARY: nothing is deployed by this file.  It is NOT applied to
-- any live environment by Storage Management Step 2; it is listed in the Step 2
-- report as a migration that must be applied by the normal authorised
-- deployment process.  Until it is applied, the live storage-layer cap may still
-- be below the application limit (recorded as an open deployment dependency).
-- ============================================================================

DO $ct_step2_documents_bucket_alignment$
DECLARE
    ratified_limit constant bigint := 10485760;  -- 10 MiB, mirrors upload_limits.py
    current_limit bigint;
    current_public boolean;
BEGIN
    IF to_regclass('storage.buckets') IS NULL THEN
        RAISE NOTICE
            'Storage Step 2I: storage layer not provisioned in this database — '
            'bucket-level size limit not applicable (application-level limits '
            'remain in force).';
        RETURN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE name = 'documents') THEN
        RAISE NOTICE
            'Storage Step 2I: bucket "documents" is absent in this database — '
            'nothing to align (provision storage before applying the chain).';
        RETURN;
    END IF;

    -- Align to the ratified cap in either direction (see the header note).
    UPDATE storage.buckets
       SET file_size_limit = ratified_limit
     WHERE name = 'documents'
       AND (file_size_limit IS NULL OR file_size_limit <> ratified_limit);

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

    IF current_limit IS DISTINCT FROM ratified_limit THEN
        RAISE EXCEPTION
            'Storage Step 2I precondition failed: documents.file_size_limit = % '
            '(expected exactly %)', current_limit, ratified_limit;
    END IF;

    IF current_public IS TRUE THEN
        RAISE EXCEPTION
            'Storage Step 2I precondition failed: the documents bucket is public';
    END IF;

    RAISE NOTICE
        'Storage Step 2I: documents bucket aligned — file_size_limit = %, public = %',
        current_limit, current_public;
END
$ct_step2_documents_bucket_alignment$;
