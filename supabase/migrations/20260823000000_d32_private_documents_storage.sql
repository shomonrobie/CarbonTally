-- ============================================================================
-- D32 (P0) — PRIVATE document storage
-- ----------------------------------------------------------------------------
-- Security hardening: customer documents must never be exposed through
-- predictable/public URLs. The ``documents`` bucket becomes PRIVATE and
-- storage.objects gains org-scoped RLS so only authenticated members of the
-- owning organisation can read/manage the objects under ``uploads/<org_id>/``.
--
-- The V3 API serves documents exclusively through short-lived signed URLs
-- (services/storage.py + /api/v3/documents/{id}/signed-url), and the pipeline
-- workspace responses sign item URLs at read time. Service-role uploads bypass
-- RLS (unchanged); signed URL generation is server-side.
-- ============================================================================

BEGIN;

-- 1. Private bucket — public URLs are no longer served for any object.
UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';

-- 2. Org-scoped storage RLS (object path layout: uploads/<org_id>/<date>/<file>).
--
-- P8-D17-MIGRATION-REVISION-001 (PO-authorised minimal revision): the previous
-- `ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY` is NOT issued here.
-- `storage.objects` is owned by Supabase's provider-managed role
-- (`supabase_storage_admin`), and ALTER TABLE requires ownership even when the
-- change is a no-op. RLS is already enabled on `storage.objects` in every
-- environment this migration targets, so the statement was a semantic no-op that
-- could only ever fail on the ownership check. The read-only assertion below
-- replaces it: it needs no ownership, and it fails loudly if the precondition is
-- ever untrue, so the intended end state cannot silently regress.
DO $d32_rls$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'storage' AND c.relname = 'objects' AND c.relrowsecurity
    ) THEN
        RAISE EXCEPTION 'D32 precondition failed: RLS is not enabled on storage.objects';
    END IF;
END
$d32_rls$;

CREATE POLICY "d32_documents_select_org_member" ON storage.objects
  FOR SELECT TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = 'uploads'
    AND (storage.foldername(name))[2]::uuid IN (
      SELECT organization_id FROM public.organization_members
      WHERE user_id = auth.uid() AND is_active = TRUE
    )
  );

CREATE POLICY "d32_documents_insert_org_member" ON storage.objects
  FOR INSERT TO authenticated
  WITH CHECK (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = 'uploads'
    AND (storage.foldername(name))[2]::uuid IN (
      SELECT organization_id FROM public.organization_members
      WHERE user_id = auth.uid() AND is_active = TRUE
    )
  );

CREATE POLICY "d32_documents_update_org_member" ON storage.objects
  FOR UPDATE TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = 'uploads'
    AND (storage.foldername(name))[2]::uuid IN (
      SELECT organization_id FROM public.organization_members
      WHERE user_id = auth.uid() AND is_active = TRUE
    )
  );

CREATE POLICY "d32_documents_delete_org_member" ON storage.objects
  FOR DELETE TO authenticated
  USING (
    bucket_id = 'documents'
    AND (storage.foldername(name))[1] = 'uploads'
    AND (storage.foldername(name))[2]::uuid IN (
      SELECT organization_id FROM public.organization_members
      WHERE user_id = auth.uid() AND is_active = TRUE
    )
  );

COMMIT;
