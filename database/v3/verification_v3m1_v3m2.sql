-- ============================================================================
-- CarbonTally V3 — Implementation Phase 1, Verification SQL (read-only)
-- File: database/v3/verification_v3m1_v3m2.sql
--
-- Read-only verification of V3M-1 + V3M-2 (Processing Entity foundation and
-- work-item entity relationships). No DML/DDL — SELECT/checks only.
--
-- Expected:
--   * processing_entities table exists (RLS enabled, NO policies)
--   * staff_profiles.entity_id / manual_review_queue.entity_id /
--     upload_batches.entity_id exist (nullable UUID)
--   * Three entity FKs exist with confdeltype = 'r' (ON DELETE RESTRICT)
--   * Three entity indexes exist
--   * Factor baseline: DEFRA-DESNZ 7,029 · SEAI 20 · TOTAL 7,049
-- ============================================================================

-- 1. processing_entities table + RLS + policies
SELECT
    c.relname                                  AS table_name,
    c.relrowsecurity                           AS rls_enabled,
    (SELECT count(*) FROM pg_policies p
      WHERE p.schemaname = 'public' AND p.tablename = c.relname) AS policy_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname = 'processing_entities';

-- 2. New entity_id columns (should each return exactly one nullable row)
SELECT table_name, column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name = 'entity_id'
  AND table_name IN ('staff_profiles','manual_review_queue','upload_batches')
ORDER BY table_name;

-- 3. Entity FKs (should return three rows, confdeltype 'r' = RESTRICT)
SELECT conname, confdeltype, pg_get_constraintdef(oid) AS def
FROM pg_constraint
WHERE conname IN (
    'staff_profiles_entity_id_fkey',
    'manual_review_queue_entity_id_fkey',
    'upload_batches_entity_id_fkey'
)
ORDER BY conname;

-- 4. Entity indexes (should return three rows)
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'idx_staff_profiles_entity_id',
    'idx_manual_review_queue_entity_id',
    'idx_upload_batches_entity_id'
  )
ORDER BY indexname;

-- 5. Factor baseline invariant (read-only count — must be exactly 7,049)
SELECT count(*) AS total_factors FROM public.emission_factors;

SELECT factor_source, country, count(*) AS n
FROM public.emission_factors
GROUP BY factor_source, country
ORDER BY factor_source, country;
-- Expect: DEFRA-DESNZ / GB = 7,029 ; SEAI / IE = 20 ; total = 7,049

-- 6. No entity-scoped policies created (deny-by-default floor)
SELECT count(*) AS processing_entities_policy_count
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'processing_entities';
-- Expect: 0 (ADR-V3-010 policies deferred)
