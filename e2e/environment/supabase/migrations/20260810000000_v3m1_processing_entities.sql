-- ============================================================================
-- CarbonTally V3 — Implementation Phase 1, Migration V3M-1
-- File: 20260810000000_v3m1_processing_entities.sql
--
-- Implements the approved Processing Entity foundation (ADR-V3-001 — DECIDED,
-- Option B: dedicated `processing_entities` table; V3 IA §8 V3M-1).
--
-- Scope (strictly V3M-1 — NOT V3M-3 / V3M-5 / V3M-4):
--   * processing_entities   (NEW table — first-class entity domain)
--   * staff_profiles.entity_id (EXTEND — nullable FK to processing_entities)
--
-- Approved convention (register ADR-V3-001; spec §7.1):
--   * staff_profiles.entity_id IS NULL     = CarbonTally internal processing
--   * staff_profiles.entity_id = <pe.id>   = staff belonging to a Processing Entity
--   * NULL is a POSITIVE value (CarbonTally internal) — never "unknown"/"missing".
--
-- Lifecycle (ADR-V3-001 Q6 clarifications — PROVISIONALLY DECIDED):
--   * status VARCHAR + CHECK (active / remediation / suspended / terminated);
--     exact state vocabulary finalized in V3 design, kept minimal here.
--   * Suspension/termination NEVER deletes historical work, audit, performance
--     or issue history — entity rows are never hard-deleted while referenced.
--   * FK ON DELETE RESTRICT: an entity with referencing staff/work cannot be
--     hard-deleted (the NULL convention must not be silently corrupted by a
--     SET NULL that would turn entity staff into "CarbonTally internal").
--
-- Contract metadata (Q1 — PROVISIONALLY DECIDED): recognised as part of the
-- Processing Entity domain; exact commercial fields / pricing / contract schema
-- are DEFERRED to V3 schema design. A generic `metadata JSONB` column carries
-- contract/commercial information flexibly without inventing final columns.
--
-- RLS (ADR-V3-010 — PROVISIONALLY DECIDED): only the deny-by-default floor is
-- applied here (ENABLE RLS + service_role/authenticated grants, NO policies),
-- following the M8 convention. Entity-scoped access policies (is_entity_member)
-- belong to ADR-V3-010 and are NOT created in this migration.
--
-- Non-destructive and additive; existing staff rows remain valid (entity_id
-- defaults NULL = CarbonTally internal). No factor data is touched.
-- Idempotent: CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS, guarded FK,
-- CREATE INDEX IF NOT EXISTS, idempotent grants/RLS enablement.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. processing_entities (NEW)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.processing_entities (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','remediation','suspended','terminated')),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

COMMENT ON TABLE public.processing_entities IS
    'First-class Human Data Processing Entity (ADR-V3-001 — Option B, dedicated table). '
    'Distinct from Customer/Organization, User, Entity Staff, Consultant and CarbonTally '
    'internal staff. Lifecycle: active / remediation / suspended / terminated. Contract '
    'metadata fields deferred to V3 schema design (Q1) — carried in metadata JSONB.';
COMMENT ON COLUMN public.processing_entities.status IS
    'Lifecycle status (Q6): active / remediation / suspended / terminated. Entity rows are '
    'never hard-deleted while referenced; lifecycle changes preserve history.';
COMMENT ON COLUMN public.processing_entities.metadata IS
    'Flexible contract/commercial metadata (Q1 — exact fields deferred to V3 design).';

-- ---------------------------------------------------------------------------
-- 2. staff_profiles.entity_id (EXTEND)
--    NULL = CarbonTally internal processing; populated = Processing Entity staff.
-- ---------------------------------------------------------------------------
ALTER TABLE public.staff_profiles
    ADD COLUMN IF NOT EXISTS entity_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'staff_profiles_entity_id_fkey'
    ) THEN
        ALTER TABLE public.staff_profiles
            ADD CONSTRAINT staff_profiles_entity_id_fkey
            FOREIGN KEY (entity_id) REFERENCES public.processing_entities(id)
            ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_staff_profiles_entity_id
    ON public.staff_profiles (entity_id);

COMMENT ON COLUMN public.staff_profiles.entity_id IS
    'NULL = CarbonTally internal processing staff (positive convention, NOT unknown). '
    'Populated = staff member belonging to the referenced Processing Entity '
    '(ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution; entity rows are never '
    'hard-deleted while staff reference them.';

-- ---------------------------------------------------------------------------
-- 3. RLS — deny-by-default floor (M8 convention; entity policies deferred to ADR-V3-010)
-- ---------------------------------------------------------------------------
ALTER TABLE public.processing_entities ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.processing_entities TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.processing_entities TO authenticated;
REVOKE TRUNCATE, TRIGGER, REFERENCES, MAINTAIN ON TABLE public.processing_entities FROM authenticated;

-- NO policies are created: processing_entities is deny-by-default for
-- authenticated until ADR-V3-010 defines entity-scoped access (is_entity_member).

-- ============================================================================
-- VERIFICATION CHECKLIST (V3M-1)
--   [ ] processing_entities table exists (id, name, status CHECK, metadata, timestamps)
--   [ ] staff_profiles.entity_id exists (nullable UUID)
--   [ ] FK staff_profiles_entity_id_fkey → processing_entities(id) ON DELETE RESTRICT
--   [ ] Index idx_staff_profiles_entity_id exists
--   [ ] Existing staff rows untouched; entity_id = NULL (= CarbonTally internal)
--   [ ] RLS enabled on processing_entities; service_role ALL; authenticated DML (no TRUNCATE)
--   [ ] No entity-scoped policies created (deferred to ADR-V3-010)
--   [ ] Factor baseline untouched (DEFRA 7,029 · SEAI 20 · TOTAL 7,049)
--   [ ] Re-running this file is a no-op
-- ============================================================================

