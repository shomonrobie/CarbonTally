-- ============================================================================
-- P17-D — Scope 3 category taxonomy (reference seed, exactly 15 rows)
-- File: 20261012000000_p17d_scope3_category_taxonomy.sql
--
-- Authority: docs/architecture/artifacts/p17_schema_delta_20250925.md §3.3.
--
-- Why: `calculation_snapshots.scope3_category` is constrained to 1..15, but
-- nothing named those categories. Without a controlled vocabulary the UI cannot
-- present a category picker, reporting cannot label a category, and the
-- boundary rules (DC-04/DC-05/DC-07) cannot reference a stable identity.
--
-- Scope: REFERENCE DATA ONLY. This seeds the GHG Protocol category names. It
-- creates no methodology, no factor, no calculation, no result and no
-- implementation. Category support status (SUPPORTED / PARTIAL /
-- NOT_IMPLEMENTED / DEFERRED) is an ARCHITECTURE status carried by
-- p17_scope3_category_matrix_20250925.json and is deliberately NOT stored here -
-- a status is not reference data and putting it in a lookup table would invite
-- treating "the row exists" as "the category is implemented".
--
-- Additive only: one new reference table. No existing object is modified.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.scope3_categories (
    category      smallint PRIMARY KEY,
    slug          text NOT NULL UNIQUE,
    name          text NOT NULL,
    is_downstream boolean NOT NULL DEFAULT false,
    description   text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT scope3_categories_range_check CHECK (category BETWEEN 1 AND 15)
);

COMMENT ON TABLE public.scope3_categories IS
    'P17-D: the controlled 15-category GHG Protocol Scope 3 vocabulary behind calculation_snapshots.scope3_category and the DC-04/DC-05/DC-07 boundary rules. Reference data only - it does NOT imply that a category has a supported methodology.';
COMMENT ON COLUMN public.scope3_categories.is_downstream IS
    'P17-D: GHG Protocol downstream classification. Used by boundary presentation and by the category 4 vs 9 / 5 vs 12 / 8 vs 13 discriminators.';

INSERT INTO public.scope3_categories (category, slug, name, is_downstream, description) VALUES
 (1,  'purchased_goods_and_services',            'Purchased goods and services',            false, 'Extraction, production and transportation of goods and services purchased by the reporting company in the reporting year (cradle-to-gate).'),
 (2,  'capital_goods',                           'Capital goods',                           false, 'Extraction, production and transportation of capital goods purchased by the reporting company in the reporting year (cradle-to-gate).'),
 (3,  'fuel_and_energy_related_activities',      'Fuel- and energy-related activities',     false, 'Upstream emissions of purchased fuels, upstream emissions of purchased electricity and T&D losses (not already in Scope 1/2).'),
 (4,  'upstream_transportation_and_distribution','Upstream transportation and distribution', false, 'Transportation and distribution of purchased products and third-party transportation paid for by the reporting company.'),
 (5,  'waste_generated_in_operations',           'Waste generated in operations',           false, 'Disposal and treatment of waste generated in operations owned or controlled by the reporting company.'),
 (6,  'business_travel',                         'Business travel',                         false, 'Transportation of employees for business-related activities in vehicles not owned or operated by the reporting company.'),
 (7,  'employee_commuting',                      'Employee commuting',                      false, 'Transportation of employees between their homes and their worksites.'),
 (8,  'upstream_leased_assets',                  'Upstream leased assets',                  false, 'Operation of assets leased by the reporting company (lessee) not included in Scope 1/2.'),
 (9,  'downstream_transportation_and_distribution','Downstream transportation and distribution', true,  'Transportation and distribution of sold products paid for by the buyer, plus retail and storage.'),
 (10, 'processing_of_sold_products',             'Processing of sold products',             true,  'Processing of intermediate products sold by downstream companies.'),
 (11, 'use_of_sold_products',                    'Use of sold products',                    true,  'End use of goods and services sold by the reporting company.'),
 (12, 'end_of_life_treatment_of_sold_products',  'End-of-life treatment of sold products',  true,  'Waste disposal and treatment of products sold by the reporting company at end of life.'),
 (13, 'downstream_leased_assets',                'Downstream leased assets',                true,  'Operation of assets owned by the reporting company (lessor) and leased to other entities.'),
 (14, 'franchises',                              'Franchises',                              true,  'Operation of franchises in the reporting year, not included in Scope 1/2.'),
 (15, 'investments',                             'Investments',                             true,  'Operation of investments (including equity and debt investments and project finance) not in Scope 1/2.')
ON CONFLICT (category) DO NOTHING;

-- RLS: reference data. Any authenticated principal may read it; only the service
-- role may write it. anon gets nothing.
ALTER TABLE public.scope3_categories ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.scope3_categories FROM anon;
GRANT SELECT ON TABLE public.scope3_categories TO authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES, MAINTAIN
    ON TABLE public.scope3_categories FROM authenticated;
GRANT ALL ON TABLE public.scope3_categories TO service_role;

DROP POLICY IF EXISTS scope3_categories_read ON public.scope3_categories;
CREATE POLICY scope3_categories_read
    ON public.scope3_categories FOR SELECT TO authenticated
    USING (true);

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-D)
--   [ ] scope3_categories exists with EXACTLY 15 rows (1..15)
--   [ ] slug is unique; category is the PK
--   [ ] authenticated may SELECT only; anon none; service_role ALL
--   [ ] NO methodology / factor / calculation row created
--   [ ] re-running this file seeds nothing new (ON CONFLICT DO NOTHING)
-- ============================================================================
