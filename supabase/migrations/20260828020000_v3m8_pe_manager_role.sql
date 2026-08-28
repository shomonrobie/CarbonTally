-- ============================================================================
-- CarbonTally V3 — PO Decision 4: PE Manager extraction role
-- File: 20260828020000_v3m8_pe_manager_role.sql
--
-- PO Decision 4 (APPROVED): the PE Manager must be able to operate assigned
-- extraction work (see assigned batches, open the extraction workspace, work
-- on assigned items, see PE-level operational information) WITHOUT becoming a
-- customer-org owner and WITHOUT weakening the PE no-download / source-document
-- boundary.
--
-- Root cause (ISC-14): the 3 demo PE Managers shared the internal ``reviewer``
-- staff role (``can_review`` only), so the entity extraction workspace (which
-- requires ``can_process``) returned 403.
--
-- Fix: a dedicated ``pe_manager`` staff role with the extraction permission
-- (``can_process``) plus the review/oversight permissions — the internal
-- ``reviewer`` role keeps its least-privilege (no expansion).
--
-- Additive; only the 3 demo PE-manager staff profiles are re-roled.
-- ============================================================================

INSERT INTO public.staff_roles (id, name, description, permissions, created_at, updated_at)
VALUES (
    '5aaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'pe_manager',
    'Processing Entity manager — operates the entity''s assigned extraction work (PO Decision 4)',
    '{"can_process": true, "can_review": true, "can_view_all": true}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    permissions = EXCLUDED.permissions,
    updated_at = NOW();

-- Re-role the demo PE managers to the dedicated role (keep their entity scope).
UPDATE public.staff_profiles
SET role_id = '5aaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
WHERE email LIKE 'pe-manager-%.demo@demo.carbontally.local'
  AND role_id = '52222222-2222-4222-8222-222222222222';

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [x] staff_roles has pe_manager with can_process + can_review + can_view_all
--   [x] pe-manager-*.demo profiles use the pe_manager role
--   [x] internal reviewer role (52222222-...) unchanged (least privilege)
-- ============================================================================
