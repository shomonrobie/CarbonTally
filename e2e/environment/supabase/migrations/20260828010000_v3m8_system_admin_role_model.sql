-- ============================================================================
-- CarbonTally V3 — PO Decision 2: system_admin role-model + CL-22 test-role
-- File: 20260828010000_v3m8_system_admin_role_model.sql
--
-- PO Decision 2 (APPROVED): ``system_admin`` is a full system-administration
-- role and must be a superset of the legacy ``admin`` staff role (audit/billing/
-- retention/control-plane). Root cause (ISC-10): the seeded ``system_admin``
-- role lacked ``can_manage_billing`` and the legacy ``/api/v2/admin/*``
-- authorizer only recognised the literal role name ``admin``. The authorizer
-- fix lives in ``backend/auth.py`` (ADMIN_ROLE_NAMES); this migration fixes the
-- authoritative permission catalog.
--
-- CL-22: the stray test role ``t_ba_34e3cb`` (staff_roles) was created by a
-- test run; it is identified by the audits as invalid legacy/test data and is
-- removed together with its test-only staff profile.
--
-- Additive/idempotent where possible; the test-role removal is a one-time,
-- audit-identified data cleanup.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. system_admin permission superset (add can_manage_billing)
-- ---------------------------------------------------------------------------
UPDATE public.staff_roles
SET permissions = permissions || '{"can_manage_billing": true}'::jsonb,
    updated_at = NOW()
WHERE name = 'system_admin'
  AND (permissions->>'can_manage_billing') IS DISTINCT FROM 'true';

-- ---------------------------------------------------------------------------
-- 2. Remove the stray test role + its test-only staff profile (CL-22)
-- ---------------------------------------------------------------------------
DELETE FROM public.staff_profiles
WHERE role_id = '56f5fa09-30d8-43a7-a5be-fdb3fbc93519'
  AND email = 'm34e3cb22-0@t.test';

DELETE FROM public.staff_roles
WHERE id = '56f5fa09-30d8-43a7-a5be-fdb3fbc93519';

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [x] system_admin.permissions contains can_manage_billing: true
--   [x] t_ba_34e3cb test role removed (no staff profile references it)
-- ============================================================================
