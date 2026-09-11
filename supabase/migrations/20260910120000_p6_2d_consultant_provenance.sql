-- ============================================================================
-- P6-2D — Consultant firm provenance + durable processing-mode provenance (D7)
-- ----------------------------------------------------------------------------
-- Ratified under PO-PHASE6-D7-R-20260910 ("firm provenance + relevant
-- processing-mode provenance"), PO-PHASE6-D7c-R-20260910 ("no historical
-- backfill") and recorded in
-- docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md §6.2.
--
-- ADDITIVE + NULLABLE + IDEMPOTENT + BACKWARD-COMPATIBLE.
--
-- What this migration adds (manual_extraction_items only):
--   * consultant_firm_id        — the consultant FIRM that established durable
--                                 consultant processing provenance on the item.
--                                 Server-derived from the authorized
--                                 consultant membership/engagement relationship
--                                 at action time; NEVER actor-supplied.
--   * processing_mode           — the item's canonical processing-mode
--                                 classification at that same boundary:
--                                 'automatic' | 'manual'. Distinct from
--                                 processing_origin (which stays a two-value
--                                 internal/PE control-path vocabulary).
--   * consultant_provenance_at  — when the provenance above was recorded.
--
-- Deliberate constraints preserved:
--   * NO historical backfill (D7c): no UPDATE, no DEFAULT that fabricates a
--     value, no derivation from historical membership/grant rows. Existing
--     rows keep NULL provenance — historically honest.
--   * processing_origin is UNTOUCHED: its CHECK vocabulary stays exactly
--     ('CARBONTALLY_INTERNAL','PROCESSING_ENTITY'); no CONSULTANT value is
--     introduced (D7b remains withdrawn).
--   * NO RLS change: the new columns inherit the table's existing RLS posture.
--     No policy is created, dropped or altered here.
--   * No other table is touched.
--
-- Write-once semantics: the application only ever sets these columns when
-- consultant_firm_id IS NULL, so later actions, later firms, later membership
-- or engagement changes can never rewrite recorded provenance.
-- ============================================================================

ALTER TABLE public.manual_extraction_items
    ADD COLUMN IF NOT EXISTS consultant_firm_id uuid
        REFERENCES public.consultant_profiles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS processing_mode text,
    ADD COLUMN IF NOT EXISTS consultant_provenance_at timestamptz;

-- Additive CHECK on the NEW nullable column only (NULL — i.e. provenance never
-- recorded, including every pre-migration row — remains valid).
ALTER TABLE public.manual_extraction_items
    DROP CONSTRAINT IF EXISTS manual_extraction_items_processing_mode_check;

ALTER TABLE public.manual_extraction_items
    ADD CONSTRAINT manual_extraction_items_processing_mode_check
    CHECK (processing_mode IS NULL OR processing_mode IN ('automatic', 'manual'));

COMMENT ON COLUMN public.manual_extraction_items.consultant_firm_id IS
    'P6-2D (D7): consultant firm that FIRST established durable consultant '
    'processing provenance on this item (server-derived at action time; '
    'write-once; never actor-supplied; no historical backfill).';

COMMENT ON COLUMN public.manual_extraction_items.processing_mode IS
    'P6-2D (D7): canonical processing-mode classification recorded at the '
    'provenance boundary (''automatic'' | ''manual''; P1 containment predicate '
    'evaluated server-side). Separate from processing_origin, which remains the '
    'CARBONTALLY_INTERNAL/PROCESSING_ENTITY control path.';

COMMENT ON COLUMN public.manual_extraction_items.consultant_provenance_at IS
    'P6-2D (D7): when consultant_firm_id / processing_mode provenance was '
    'recorded (write-once, set with the provenance itself).';

-- ---------------------------------------------------------------------------
-- Verification checklist (P6-2D)
--   [x] Columns added with ADD COLUMN IF NOT EXISTS (idempotent)
--   [x] All three columns NULLABLE; no DEFAULT; no NOT NULL
--   [x] No UPDATE / backfill of any existing row (D7c)
--   [x] consultant_firm_id is a real FK to consultant_profiles(id) (SET NULL —
--       never blocks an existing firm-deletion flow)
--   [x] processing_mode constrained to the two-word vocabulary, NULL allowed
--   [x] processing_origin constraint + vocabulary untouched
--   [x] No RLS policy created/dropped/altered
--   [x] No other table modified
-- ============================================================================
