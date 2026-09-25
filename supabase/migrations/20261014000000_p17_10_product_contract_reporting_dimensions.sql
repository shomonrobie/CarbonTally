-- ============================================================================
-- P17-IMPLEMENT-10 — Product-contract reporting dimensions
-- File: 20261014000000_p17_10_product_contract_reporting_dimensions.sql
--
-- Authority (the PRODUCT contract, not an inference):
--   * docs/architecture/P17-PRODUCT-01 — ... Product Specification.md
--       §4  Canonical Activity model  (`supplier_id`, `supplier_name`,
--           `transaction_provider`, `methodology`, `data_quality`)
--       §5  "Transaction provider vs actual supplier" — store BOTH:
--           `transaction_provider = Booking.com`, `underlying_supplier = Hotel ABC`
--       §7  Data-quality model (8 classifications)
--       §29 Reporting model — Scope 2 location/market, Scope 3 cat 1-15,
--           plus Data quality, Methodology, Manual-review % and Unresolved %
--       §30 Investor dashboard — Primary data / Activity based / Average data /
--           Spend based / Estimated / Manual review
--       §34 "Must have" — category-specific methodology
--   * backend/domain/scope3_contracts.py — the 15 category method vocabularies
--
-- Why each statement exists
-- -------------------------
-- 1. `scope3_method` — P17-PRODUCT-01 §29 requires the reporting layer to expose
--    the METHODOLOGY of every Scope 3 category, and §34 lists "category-specific
--    methodology" as a must-have. The existing `methodology` column carries the
--    ENGINE arithmetic label (`direct_multiply` / `distance_based` / ...), which
--    is a different fact: it cannot express `supplier_specific`, `average_data`,
--    `survey_based` and the other category methods. Without this column the
--    platform can neither store nor report the method it actually used.
--
-- 2. `transaction_provider` — P17-PRODUCT-01 §5: the party someone PURCHASED
--    from (Booking.com, Agoda, Expedia, Uber, Trainline) is not the party whose
--    activity GENERATED the emissions (the hotel, the rail operator). §4 lists
--    it as a first-class canonical-activity field. It is deliberately a NAME
--    (text), not a supplier foreign key: it is an external counterparty that has
--    no reason to exist in the reporting tenant's own `suppliers` master data.
--    Storing the pair is what prevents "where we bought it" being reported as
--    "what emitted".
--
-- 3. The widened `data_quality` CHECK — P17-PRODUCT-01 §7 classifies activity as
--    PRIMARY, SUPPLIER_SPECIFIC, ACTIVITY_BASED, AVERAGE_DATA, SPEND_BASED,
--    ESTIMATED, MANUAL, UNRESOLVED, and §29/§30 require the reporting layer to be
--    able to distinguish "activity based", "estimated", "manual review" and
--    "unresolved". The P17-A vocabulary had no member for ACTIVITY_BASED,
--    ESTIMATED, MANUAL or UNRESOLVED, so four product classifications were
--    unexpressible. The CHECK is WIDENED (a strict superset) to add exactly
--    those four: `activity_based`, `estimated`, `manual`, `unresolved`.
--    NO EXISTING VALUE IS REMOVED, so every historical row stays valid and
--    nothing is narrowed. `modelled` is retained because P17-PRODUCT-01 §7's list
--    is introduced with "For example" and category 15's contract method
--    vocabulary already uses `modelled`; removing it would invalidate stored
--    rows, which this migration must never do.
--
-- Discipline (P16/P17-preserving):
--   * ADDITIVE ONLY. No column, row, value, index or policy is dropped, renamed
--     or rewritten. No historical migration is modified.
--   * Both new columns are NULLABLE with NO DEFAULT, so every existing
--     calculation_snapshots and emissions_logs row keeps its exact value and
--     meaning and receives NULL — explicitly "no method / no provider recorded",
--     never a fabricated one. NO BACKFILL IS PERFORMED.
--   * The one scope rule that new writes must satisfy is added NOT VALID, so
--     historical rows are exempt while every subsequent INSERT/UPDATE is
--     enforced (the P17-A pattern).
--   * Idempotent: every statement is IF NOT EXISTS / DROP CONSTRAINT IF EXISTS.
--
-- RLS: this migration adds no table and therefore changes no policy. It only adds
-- columns to tables that already have their RLS posture; the new columns inherit
-- it. No RLS is weakened and no authorization behaviour changes.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. calculation_snapshots — the authoritative calculation record
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots
    ADD COLUMN IF NOT EXISTS scope3_method        text,
    ADD COLUMN IF NOT EXISTS transaction_provider text;

COMMENT ON COLUMN public.calculation_snapshots.scope3_method IS
    'P17-IMPLEMENT-10 / P17-PRODUCT-01 §29: the category-specific accounting METHODOLOGY selected for a Scope 3 result (supplier_specific | average_data | spend_based | distance_based | extrapolated | survey_based | asset_specific | industry_average | modelled | proxy_data). This is NOT the engine arithmetic label - that stays in `methodology` (direct_multiply | distance_based | spend_based | area_based | mass_balance). NULL for Scope 1/2 rows and for historical rows; never inferred, only ever taken from the category contract.';
COMMENT ON COLUMN public.calculation_snapshots.transaction_provider IS
    'P17-IMPLEMENT-10 / P17-PRODUCT-01 §5: where the activity was PURCHASED (Booking.com, Agoda, Expedia, Uber, Trainline) - deliberately distinct from the supplier whose activity generated the emissions. A NAME, not a suppliers FK: an external counterparty need not exist in the tenant master data. NULL means "not recorded"; it is never filled with the underlying supplier.';

-- ---------------------------------------------------------------------------
-- 2. emissions_logs — the mirrored consumption boundary (same two dimensions)
-- ---------------------------------------------------------------------------
ALTER TABLE public.emissions_logs
    ADD COLUMN IF NOT EXISTS scope3_method        text,
    ADD COLUMN IF NOT EXISTS transaction_provider text;

COMMENT ON COLUMN public.emissions_logs.scope3_method IS
    'P17-IMPLEMENT-10: mirror of calculation_snapshots.scope3_method so the reporting/read boundary can group by category methodology without a join.';
COMMENT ON COLUMN public.emissions_logs.transaction_provider IS
    'P17-IMPLEMENT-10: mirror of calculation_snapshots.transaction_provider - the purchase channel, kept strictly separate from the emissions-generating supplier.';


-- ---------------------------------------------------------------------------
-- 3. Scope 3 methodology vocabulary (P17-PRODUCT-01 §29/§34)
--    The value list is the UNION of the fifteen category method vocabularies in
--    backend/domain/scope3_contracts.py. A value outside it can never be
--    persisted; a value inside it is still only accepted when the CATEGORY
--    contract permits it (enforced in the service, which knows the category).
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope3_method_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope3_method_check
    CHECK (scope3_method IS NULL OR scope3_method IN
        ('supplier_specific', 'average_data', 'spend_based', 'distance_based',
         'extrapolated', 'survey_based', 'asset_specific', 'industry_average',
         'modelled', 'proxy_data'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope3_method_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope3_method_check
    CHECK (scope3_method IS NULL OR scope3_method IN
        ('supplier_specific', 'average_data', 'spend_based', 'distance_based',
         'extrapolated', 'survey_based', 'asset_specific', 'industry_average',
         'modelled', 'proxy_data'));

-- A category method is meaningful only on a Scope 3 result. NOT VALID so the
-- historical rows are exempt while every new write is checked.
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_scope3_method_scope_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_scope3_method_scope_check
    CHECK (scope3_method IS NULL OR scope = 'Scope 3') NOT VALID;

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_scope3_method_scope_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_scope3_method_scope_check
    CHECK (scope3_method IS NULL OR scope = 'Scope 3') NOT VALID;

-- ---------------------------------------------------------------------------
-- 4. transaction_provider shape guard
--    A purchase channel is either absent or an actual name. An empty (or
--    whitespace-only) string would be a record that claims to name a provider and
--    does not, so it is refused rather than stored as a value that reads as
--    "known".
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_transaction_provider_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_transaction_provider_check
    CHECK (transaction_provider IS NULL
           OR (length(btrim(transaction_provider)) BETWEEN 1 AND 200));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_transaction_provider_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_transaction_provider_check
    CHECK (transaction_provider IS NULL
           OR (length(btrim(transaction_provider)) BETWEEN 1 AND 200));


-- ---------------------------------------------------------------------------
-- 5. Data-quality vocabulary — WIDENED to the product classifications
--    Strict superset of the P17-A list: the five existing values are preserved
--    verbatim and four product values are added. No historical row is
--    invalidated and no value is narrowed.
-- ---------------------------------------------------------------------------
ALTER TABLE public.calculation_snapshots DROP CONSTRAINT IF EXISTS calc_snapshots_data_quality_check;
ALTER TABLE public.calculation_snapshots ADD CONSTRAINT calc_snapshots_data_quality_check
    CHECK (data_quality IS NULL OR data_quality IN
        ('primary_measured', 'primary_supplier', 'secondary_estimated',
         'spend_based_estimated', 'modelled',
         'activity_based', 'estimated', 'manual', 'unresolved'));

ALTER TABLE public.emissions_logs DROP CONSTRAINT IF EXISTS emissions_logs_data_quality_check;
ALTER TABLE public.emissions_logs ADD CONSTRAINT emissions_logs_data_quality_check
    CHECK (data_quality IS NULL OR data_quality IN
        ('primary_measured', 'primary_supplier', 'secondary_estimated',
         'spend_based_estimated', 'modelled',
         'activity_based', 'estimated', 'manual', 'unresolved'));

COMMENT ON CONSTRAINT calc_snapshots_data_quality_check ON public.calculation_snapshots IS
    'P17-IMPLEMENT-10 / P17-PRODUCT-01 §7-§30: the five P17-A classifications plus the four product classifications (activity_based, estimated, manual, unresolved) required by the §29/§30 reporting buckets. Widened, never narrowed: no historical row was invalidated. No numeric uncertainty is implied.';
COMMENT ON CONSTRAINT emissions_logs_data_quality_check ON public.emissions_logs IS
    'P17-IMPLEMENT-10: the same widened data-quality vocabulary as calculation_snapshots.';

-- ---------------------------------------------------------------------------
-- 6. Reporting / read indexes — the §29 category-level projections
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_scope3_method
    ON public.emissions_logs (organization_id, scope3_method);
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_data_quality
    ON public.emissions_logs (organization_id, data_quality);
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_transaction_provider
    ON public.emissions_logs (organization_id, transaction_provider);
CREATE INDEX IF NOT EXISTS idx_emissions_logs_org_energy_type
    ON public.emissions_logs (organization_id, energy_type);

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-IMPLEMENT-10)
--   [ ] 2 new columns on calculation_snapshots (scope3_method, transaction_provider)
--   [ ] 2 mirrors present on emissions_logs
--   [ ] scope3_method vocabulary CHECK on both tables (10 contract methods)
--   [ ] scope3_method is NULL or scope = 'Scope 3' (NOT VALID, new writes only)
--   [ ] transaction_provider is NULL or a non-blank name of 1..200 chars
--   [ ] data_quality CHECK WIDENED to 9 values on both tables (superset)
--   [ ] every historical row byte-identical; NO backfill performed
--   [ ] re-running this file is a no-op
--   [ ] NO RLS policy altered; NO table created; NO value removed
-- ============================================================================

