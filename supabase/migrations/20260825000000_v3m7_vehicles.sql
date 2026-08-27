-- ============================================================================
-- CarbonTally V3 — D17 master data: Vehicles (G-P1-2 closure)
-- File: 20260825000000_v3m7_vehicles.sql
--
-- Implements the frozen D17 organisation master-data model:
--     Organisation → Locations → Facilities → {Assets, Vehicles}; Suppliers
-- org-scoped.
--
-- Engineering decision (N2 — Location physical representation): Locations are
-- NOT a separate table. The existing `facilities` entity already doubles as
-- the "facilities/locations" surface (full address fields + a `type`
-- discriminator). Vehicles are the one D17 master-data entity that had no
-- physical representation, so a dedicated org-scoped `vehicles` table is
-- created here (the minimum necessary change).
--
-- RLS (reuses the RC2/M8 conventions exactly as customer_factors V3M-3):
--   * RLS enabled; service_role ALL; authenticated DML (no TRUNCATE/TRIGGER/
--     REFERENCES/MAINTAIN).
--   * SELECT = org member OR authorised consultant (existing consultant-client
--     RLS model) — master data is visible to the org's consultants.
--   * INSERT / UPDATE / DELETE = org member only (org-scoped via
--     `organization_id`); matching the facilities DELETE surface already used
--     by the customer admin UI.
--
-- Safety: additive and idempotent (CREATE TABLE IF NOT EXISTS, guarded
-- policies, guarded indexes). No existing table, row or policy is altered.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. vehicles (NEW)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.vehicles (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    registration VARCHAR,
    make VARCHAR,
    model VARCHAR,
    fuel_type VARCHAR,
    vehicle_type VARCHAR,
    capacity NUMERIC CHECK (capacity IS NULL OR capacity >= 0),
    capacity_unit VARCHAR,
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

COMMENT ON TABLE public.vehicles IS
    'Organisation-scoped fleet master data (D17). Vehicles are first-class master-data entities; they are org-scoped and secondary to the processing pipeline (D17/D18).';
COMMENT ON COLUMN public.vehicles.organization_id IS
    'Owning organisation. RLS is scoped to this column (org isolation).';
COMMENT ON COLUMN public.vehicles.fuel_type IS
    'Free-text fuel descriptor (e.g. diesel, petrol, electric, hybrid) used for extraction mapping candidates; never an emission authority.';

-- ---------------------------------------------------------------------------
-- 2. Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_vehicles_organization_id ON public.vehicles (organization_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_org_active ON public.vehicles (organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_vehicles_org_fuel ON public.vehicles (organization_id, fuel_type);

-- ---------------------------------------------------------------------------
-- 3. updated_at trigger (existing convention)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trg_set_updated_at_vehicles() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_updated_at_vehicles ON public.vehicles;
CREATE TRIGGER trg_set_updated_at_vehicles
    BEFORE UPDATE ON public.vehicles
    FOR EACH ROW
    EXECUTE FUNCTION public.trg_set_updated_at_vehicles();

-- ---------------------------------------------------------------------------
-- 4. RLS — deny-by-default, org-scoped
-- ---------------------------------------------------------------------------
ALTER TABLE public.vehicles ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.vehicles TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.vehicles TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.vehicles FROM authenticated;

-- SELECT: org member OR authorised consultant (existing consultant-client model).
DROP POLICY IF EXISTS vehicles_select_own ON public.vehicles;
CREATE POLICY vehicles_select_own ON public.vehicles
    FOR SELECT TO authenticated
    USING (
        public.is_org_member(organization_id)
        OR public.is_org_consultant(organization_id)
    );

-- INSERT: org member only.
DROP POLICY IF EXISTS vehicles_insert_own ON public.vehicles;
CREATE POLICY vehicles_insert_own ON public.vehicles
    FOR INSERT TO authenticated
    WITH CHECK (
        public.is_org_member(organization_id)
    );

-- UPDATE: org member only.
DROP POLICY IF EXISTS vehicles_update_own ON public.vehicles;
CREATE POLICY vehicles_update_own ON public.vehicles
    FOR UPDATE TO authenticated
    USING (public.is_org_member(organization_id))
    WITH CHECK (public.is_org_member(organization_id));

-- DELETE: org member only (mirrors the facilities admin surface).
DROP POLICY IF EXISTS vehicles_delete_own ON public.vehicles;
CREATE POLICY vehicles_delete_own ON public.vehicles
    FOR DELETE TO authenticated
    USING (public.is_org_member(organization_id));

-- ============================================================================
-- VERIFICATION CHECKLIST
--   [ ] vehicles table exists (org-scoped, CHECKed capacity, metadata, audit cols)
--   [ ] RLS enabled; service_role ALL; authenticated DML (no TRUNCATE/TRIGGER/
--       REFERENCES/MAINTAIN)
--   [ ] SELECT = is_org_member OR is_org_consultant
--   [ ] INSERT / UPDATE / DELETE = is_org_member
--   [ ] updated_at trigger installed
--   [ ] indexes on org / org+active / org+fuel exist
--   [ ] Re-running this file is a no-op
-- ============================================================================

