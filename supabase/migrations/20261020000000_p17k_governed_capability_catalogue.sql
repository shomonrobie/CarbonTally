-- ============================================================================
-- P17-K — Governed capability catalogue (disclosure requirement versions)
-- File: 20261020000000_p17k_governed_capability_catalogue.sql
--
-- Authority (the PRODUCT contract, not an inference):
--   * docs/architecture/CT-PO-P17-DECISION-03-PO-FREEZE-CAPABILITY-STATUS-
--     INVESTOR-SURFACE-20250926.md
--       §18.1 Tier 2 item 7 — "Author `disclosure_requirement_versions` rows so
--                              the 15 categories (and any Scope 1/2 requirement)
--                              have a persisted governed capability value."
--       §20.3 step 3        — the P17-K task definition.
--       §5.3 `M-1`          — the internal→governed capability mapping.
--       §11.1/§11.2         — the frozen Scope 3 1–15 rollup and matrix.
--       §10.3 `SC-4`        — the Scope 2 market-based claim boundary.
--       §18.2 `F-1`/`F-2`   — forbidden: any applicability model, any new
--                              capability vocabulary/enum/status column.
--   * PQ-6 (CARBONTALLY_PHASE8_B1_PO_DECISION_RATIFICATION_20260912.md §7) —
--     framework-VERSION rows may be seeded ONLY where the identity/version
--     information is supported by authoritative evidence; version rows MUST NOT
--     be invented. The version label, source tier, source URL and status below
--     are taken verbatim from the authoritative-evidence record
--     docs/architecture/CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_
--     VERIFICATION_20260912.md (§4 source register S1; §9.0 "Framework
--     inventory (verified versions)"). Nothing is invented.
--
-- What this migration is
-- ----------------------
-- REFERENCE DATA ONLY, inserted into catalogue tables that ALREADY EXIST
-- (`disclosure_framework_versions`, `disclosure_requirement_versions`, created
-- by 20260914000000_p8_b1_disclosure_model_foundation.sql). It expresses the
-- product's capability for the Scope 1 / Scope 2 / Scope 3 requirements using
-- the governed vocabularies that already exist:
--
--   * capability : `carbontally_capability` — exactly the 7 governed
--                  `CARBONTALLY_CAPABILITIES` values (CHECK-enforced);
--   * class      : `requirement_class` — exactly the 8 governed
--                  `REQUIREMENT_CLASSES` values (CHECK-enforced).
--
-- NO new table, column, enum, CHECK, index, policy or vocabulary is created.
--
-- What this migration is NOT (hard boundaries — each is a re-opened decision)
-- -------------------------------------------------------------------------
--   * NOT a Scope 3 category applicability model (`F-1`): `requirement_class`
--     and `carbontally_capability` are properties of the REQUIREMENT VERSION
--     (a framework/product fact), never of a tenant. No tenant state exists
--     here; tenant state lives on `disclosure_applicability_assessments` /
--     `disclosure_values`, which this migration does not touch.
--   * NOT a second capability vocabulary (`F-2`).
--   * NOT a claim about any customer: no organisation, facility, period or
--     figure appears. `NOT_SUPPORTED` means "the product does not currently
--     offer it", never a statement about the customer's emissions and never an
--     applicability outcome (`NS-1`, `S3-4`, `F-1`).
--   * NOT an upgrade: architecture statuses are mapped AT THE BOUNDARY via
--     `M-1` and are deliberately NOT stored. The Axis-A tokens (`PARTIAL`,
--     `DEFERRED`, `NOT_IMPLEMENTED`) appear nowhere as a persisted value, so a
--     consumer cannot render them (`M-3`, `M-4`, `F-3`, `AG-3`).
--   * NOT history re-written: no existing row is updated or deleted; every
--     historical result stays byte-identical.
--
-- M-1 mapping actually encoded (non-upgrading, one-directional)
-- ------------------------------------------------------------
--   architecture_status  ->  carbontally_capability     (persisted here)
--   SUPPORTED            ->  SUPPORTED
--   PARTIAL              ->  PARTIALLY_SUPPORTED
--   DEFERRED             ->  FUTURE
--   NOT_IMPLEMENTED      ->  MISSING_CAPABILITY
--
-- `requirement_class` is the framework-side classification (Scope 1/2 =
-- REQUIRED per the evidence record's GP-S1/GP-S2 rows; Scope 3 = CONDITIONAL
-- per its GP-S3 row). It is NOT set to `NOT_SUPPORTED`/`FUTURE`: those are
-- PRODUCT outcomes, derived at projection time from the capability by the
-- existing engine (`backend/domain/disclosure_projection.py::
-- derive_effective_class`: `MISSING_CAPABILITY` -> `NOT_SUPPORTED`; `FUTURE` ->
-- `FUTURE`). Writing a product outcome into the framework classification would
-- conflate the two axes (`NS-1`, `PQ-3`).
--
-- Idempotent: every statement is guarded, so re-running this file is a no-op.
-- Additive only: no existing object is modified. No RLS policy is changed (both
-- tables already carry the global-catalogue posture: authenticated SELECT,
-- service-role write, anon denied).
-- ============================================================================


-- ---------------------------------------------------------------------------
-- 0. Pre-condition — the Phase 8 B1 identities must exist.
--
--    Deliberately FAILS LOUDLY rather than inserting nothing. Without the
--    `GHG_PROTOCOL` framework identity (seeded by 20260914000000) every INSERT
--    below would silently match zero rows and this migration would appear to
--    succeed while producing an empty catalogue — the exact "false completion"
--    `AGENTS.md §74` forbids.
-- ---------------------------------------------------------------------------
DO $$
DECLARE n integer;
BEGIN
    SELECT count(*) INTO n
      FROM public.disclosure_frameworks
     WHERE code = 'GHG_PROTOCOL';
    IF n <> 1 THEN
        RAISE EXCEPTION
            'P17-K: the GHG_PROTOCOL framework identity is absent (rows = %). Apply the Phase 8 B1 disclosure foundation (20260914000000_p8_b1_disclosure_model_foundation.sql) first.', n;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. The GHG Protocol framework version this catalogue hangs off
--    (PQ-6 — evidenced, never invented.)
--
--    `disclosure_requirement_versions.framework_version_id` is NOT NULL, so a
--    requirement cannot exist without a version row. The version identity is the
--    one the authoritative-evidence record binds for the primary accounting
--    foundation (§9.0): "Corporate Accounting and Reporting Standard, 2004
--    revised edition" (+ Scope 2 Guidance 2015; Scope 3 Standard; Feb-2013
--    gases/GWP amendment), source register S1, tier 1.
--
--    Fields deliberately left NULL, with the reason:
--      * `legal_reference`           — the GHG Protocol is a voluntary standard,
--                                      not a legal instrument.
--      * `authoritative_source_date` — the evidence record establishes the
--                                      EDITION (named in `version_label`) but no
--                                      machine-checkable publication date, so no
--                                      date is asserted; inventing one would
--                                      breach PQ-6. The record's read date
--                                      (2026-09-12) is verification provenance,
--                                      recorded in the P17-K report, not the
--                                      source's own date.
--      * `applicable_from`           — no authoritative in-force date asserted.
--                                      (`status = 'IN_FORCE'` does not require a
--                                      date; only `ADOPTED_NOT_IN_FORCE` is
--                                      forbidden one, per the B1 CHECK.)
--
--    A companion-standard SPLIT (separate version rows for the Scope 2 Guidance
--    and the Corporate Value Chain (Scope 3) Standard) is deliberately NOT done
--    here: the evidence record names those companions but gives no authoritative
--    version label or date for them, so a version row for each would be invented
--    (PQ-6). They are named in each requirement's `source_locator` instead.
-- ---------------------------------------------------------------------------
INSERT INTO public.disclosure_framework_versions (
    framework_id, version_label, legal_reference, source_tier, source_url,
    authoritative_source_date, status, applicable_from, applicable_to,
    verified_at
)
SELECT f.id,
       'Corporate Accounting and Reporting Standard (2004 revised edition)',
       NULL,
       1,
       'https://ghgprotocol.org/corporate-standard',
       NULL,
       'IN_FORCE',
       NULL,
       NULL,
       now()
  FROM public.disclosure_frameworks f
 WHERE f.code = 'GHG_PROTOCOL'
ON CONFLICT (framework_id, version_label) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 2. Scope 1 and Scope 2 requirements (3 rows)
--
--    Scope 2 is expressed per METHOD, because the method is part of a Scope 2
--    result's identity and is never inferred or defaulted (`SC-1`, `SC-2`). The
--    method is carried by the existing CHECK-constrained `scope2_method_hint`
--    column and is NOT an applicability concept (`PO-6`, resolved in substance
--    by PO-3).
--
--    Market-based is NOT `SUPPORTED`: no market-based engine exists (§8.3,
--    §9.4 item 4, `SC-4`), so its governed capability is `MISSING_CAPABILITY`,
--    which the projection engine derives to `NOT_SUPPORTED`.
--
--    `scope_hint` uses the values `emissions_logs.scope` /
--    `calculation_snapshots.scope` actually carry, because the projection
--    service uses it as a scope selector
--    (`backend/services/disclosure_projection.py:102` →
--    `data/disclosure_projection.py::load_calculation_rows`).
-- ---------------------------------------------------------------------------
INSERT INTO public.disclosure_requirement_versions (
    framework_version_id, requirement_code, official_identifier,
    identifier_status, title, description, requirement_class, is_quantitative,
    value_kind, unit_hint, scope_hint, scope2_method_hint, period_semantics,
    display_order, carbontally_capability, source_locator,
    authoritative_text_ref, source_tier, verified_at
)
SELECT fv.id,
       r.requirement_code,
       NULL,
       'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION',
       r.title,
       r.description,
       r.requirement_class,
       TRUE,
       'QUANTITATIVE',
       'kgCO2e',
       r.scope_hint,
       r.scope2_method_hint,
       'ANNUAL',
       r.display_order,
       r.carbontally_capability,
       r.source_locator,
       'GHG Protocol Corporate Standard (2004 revised edition) — Chapter 9 '
       'required-information lists not readable (binary PDF); see '
       'CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_'
       '20260912.md §23.2',
       1,
       now()
  FROM public.disclosure_frameworks f
  JOIN public.disclosure_framework_versions fv ON fv.framework_id = f.id
 CROSS JOIN (VALUES
      ('GP-S1',
       'Scope 1 emissions',
       'Direct GHG emissions from sources owned or controlled by the reporting organisation.',
       'REQUIRED', 'Scope 1', NULL::text, 1, 'SUPPORTED',
       'GHG Protocol Corporate Standard (2004 revised edition) — Scope 1'),
      ('GP-S2-LB',
       'Scope 2 emissions — location-based',
       'Indirect GHG emissions from purchased or acquired electricity, steam, heat and cooling, accounted on the location-based method. The method is part of the result identity and is never inferred or defaulted.',
       'REQUIRED', 'Scope 2', 'LOCATION_BASED', 2, 'SUPPORTED',
       'GHG Protocol Corporate Standard (2004 revised edition) + Scope 2 Guidance (2015) — location-based'),
      ('GP-S2-MB',
       'Scope 2 emissions — market-based',
       'Indirect GHG emissions from purchased or acquired electricity, steam, heat and cooling, accounted on the market-based method using contractual instruments. No market-based engine is available, so this requirement is expected but not producible; location-based and market-based results are never summed, netted or reconciled.',
       'REQUIRED', 'Scope 2', 'MARKET_BASED', 3, 'MISSING_CAPABILITY',
       'GHG Protocol Corporate Standard (2004 revised edition) + Scope 2 Guidance (2015) — market-based')
  ) AS r(requirement_code, title, description, requirement_class, scope_hint,
         scope2_method_hint, display_order, carbontally_capability,
         source_locator)
 WHERE f.code = 'GHG_PROTOCOL'
   AND fv.version_label = 'Corporate Accounting and Reporting Standard (2004 revised edition)'
ON CONFLICT (framework_version_id, requirement_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 3. Scope 3 requirements — categories 1–15 (15 rows)
--
--    Category NAMES are taken from the governed P17-D reference taxonomy
--    (`scope3_categories`, 15 rows, seeded by 20261012000000_p17d…) rather than
--    restated here, so one database holds exactly one naming of a category.
--
--    `carbontally_capability` is the `M-1` image of the frozen category matrix
--    (P17-DECISION-03 §11.1/§11.2):
--      SUPPORTED        [3, 4, 5, 6]         → 'SUPPORTED'           (4 of 15)
--      PARTIAL          [1, 7, 8, 9, 12, 13] → 'PARTIALLY_SUPPORTED' (6 of 15)
--      DEFERRED         [11, 14, 15]         → 'FUTURE'              (3 of 15)
--      NOT_IMPLEMENTED  [2, 10]              → 'MISSING_CAPABILITY'  (2 of 15)
--
--    The four-way split is therefore DERIVABLE from these rows and must never be
--    summarised as "15 categories" (`S3-1`, `AG-7`).
--
--    The Axis-A architecture tokens are written into no column and no prose:
--    "bounded scope" expresses a bounded capability and "awaiting a named
--    decision" expresses a deferral, so a consumer cannot render an internal
--    status even by copying text (`M-3`, `M-4`, `F-3`). The M-6 permitted
--    *surface* wording is a presentation rule for a future surface and is
--    deliberately not stored here.
-- ---------------------------------------------------------------------------
DO $$
DECLARE n integer;
BEGIN
    SELECT count(*) INTO n
      FROM public.scope3_categories
     WHERE category BETWEEN 1 AND 15;
    IF n <> 15 THEN
        RAISE EXCEPTION
            'P17-K: the governed Scope 3 taxonomy is incomplete (scope3_categories rows = %, expected 15). Apply 20261012000000_p17d_scope3_category_taxonomy.sql first.', n;
    END IF;
END $$;

INSERT INTO public.disclosure_requirement_versions (
    framework_version_id, requirement_code, official_identifier,
    identifier_status, title, description, requirement_class, is_quantitative,
    value_kind, unit_hint, scope_hint, scope2_method_hint, period_semantics,
    display_order, carbontally_capability, source_locator,
    authoritative_text_ref, source_tier, verified_at
)
SELECT fv.id,
       'GP-S3-CAT-' || lpad(c.category::text, 2, '0'),
       NULL,
       'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION',
       'Scope 3 category ' || c.category || ' — ' || c.name,
       m.description,
       'CONDITIONAL',
       TRUE,
       'QUANTITATIVE',
       'kgCO2e',
       'Scope 3',
       NULL,
       'ANNUAL',
       100 + c.category,
       m.carbontally_capability,
       'GHG Protocol Corporate Value Chain (Scope 3) Standard — category '
       || c.category,
       'GHG Protocol Corporate Standard (2004 revised edition) — Chapter 9 '
       'required-information lists not readable (binary PDF); see '
       'CARBONTALLY_PHASE8_REPORTING_REGULATORY_REQUIREMENT_VERIFICATION_'
       '20260912.md §23.2',
       1,
       now()
  FROM public.disclosure_frameworks f
  JOIN public.disclosure_framework_versions fv ON fv.framework_id = f.id
  JOIN public.scope3_categories c ON c.category BETWEEN 1 AND 15
 CROSS JOIN (VALUES
    (1,  'PARTIALLY_SUPPORTED', 'Goods and services purchased in the reporting year. Bounded scope; prerequisite: the canonical category dimension (P17-D) and an explicit methodology record for spend-based lines. Spend-based authorisation is an open product decision.'),
    (2,  'MISSING_CAPABILITY',  'Capital goods purchased in the reporting year. Prerequisite: a capital-goods methodology decision (supplier figure vs spend-based vs a new factor set), a category 1↔2 exclusion control and asset-level attribution.'),
    (3,  'SUPPORTED',           'Upstream emissions of purchased fuels and energy, including transmission and distribution losses not already in Scope 1 or 2. Prerequisite: the category 3 source-snapshot derivation link with its uniqueness constraint (DC-02).'),
    (4,  'SUPPORTED',           'Transportation and distribution of purchased products and third-party transportation paid for by the reporting organisation. Prerequisite: the explicit upstream/downstream boundary property (DC-04) and the mode vocabulary.'),
    (5,  'SUPPORTED',           'Disposal and treatment of waste generated in operations. Prerequisite: the category dimension on the waste path (P17-D). Reporting/disclosure end-to-end handling of the waste slice is tracked separately.'),
    (6,  'SUPPORTED',           'Transportation of employees for business-related activities in vehicles not owned or operated by the reporting organisation. Prerequisite: the well-to-tank routing rule so WTT variants land in category 3 (DC-02).'),
    (7,  'PARTIALLY_SUPPORTED', 'Transportation of employees between their homes and their worksites. Bounded scope. Prerequisite: the estimation-record entity and contract (P17-H). Whether average-data commuting estimates are authorised is an open product decision.'),
    (8,  'PARTIALLY_SUPPORTED', 'Operation of assets leased by the reporting organisation as lessee, not included in Scope 1 or 2. Bounded scope. Prerequisite: the organisation-level consolidation-approach dimension and the DC-07 duplication detector.'),
    (9,  'PARTIALLY_SUPPORTED', 'Transportation and distribution of sold products paid for by the buyer, plus retail and storage. Bounded scope. Prerequisite: the boundary property and DC-04 detector. Which element of outbound logistics is in scope is an open product decision.'),
    (10, 'MISSING_CAPABILITY',  'Processing of intermediate products sold by downstream companies. Prerequisite: a processing factor/methodology decision, a processor-declaration input contract, a sold-product entity and the DC-03 (1 vs 2 vs 10) exclusion.'),
    (11, 'FUTURE',              'End use of goods and services sold. Awaiting a named decision; prerequisite: an authorised bounded use-phase methodology and which product types are in scope, plus the assumption-set and sold-product entities.'),
    (12, 'PARTIALLY_SUPPORTED', 'Waste disposal and treatment of sold products at end of life. Bounded scope; treatment-mix assumptions must be labelled as assumptions, never as measured data. Prerequisite: the waste-origin property and DC-05 detector and a treatment-mix assumption record.'),
    (13, 'PARTIALLY_SUPPORTED', 'Operation of assets owned by the reporting organisation and leased to other entities. Bounded scope. Prerequisite: the lease-direction property and DC-07 detector, plus the consolidation-approach dimension.'),
    (14, 'FUTURE',              'Operation of franchises not included in Scope 1 or 2. Awaiting a named decision; prerequisite: the franchise operating model (whether franchisees are tenants or external parties), a franchise entity and an allocation-basis contract.'),
    (15, 'FUTURE',              'Operation of investments not included in Scope 1 or 2. Awaiting a named decision; prerequisite: ratification of the bounded attribution_equity_share methodology and an explicit position on PCAF, plus an investment entity and a lag-handling decision.')
  ) AS m(category, carbontally_capability, description)
 WHERE f.code = 'GHG_PROTOCOL'
   -- THE REQUIRED PER-CATEGORY JOIN. Without it the VALUES map would be a
   -- cross product and `ON CONFLICT DO NOTHING` would silently keep whichever
   -- row arrived first — producing a catalogue in which every category carried
   -- the same capability. (This exact defect was caught by the real-Postgres
   -- verification pass and is now also caught by the rollup post-condition
   -- in section 4.)
   AND m.category = c.category
   AND fv.version_label = 'Corporate Accounting and Reporting Standard (2004 revised edition)'
ON CONFLICT (framework_version_id, requirement_code) DO NOTHING;



-- ---------------------------------------------------------------------------
-- 4. Post-condition — the catalogue is complete, or this migration fails.
--
--    A partial catalogue is worse than an empty one: it would make a scope or
--    category silently absent from every future capability statement. The
--    expected population is 18 governed requirement rows (3 Scope 1/2 +
--    15 Scope 3) on the evidenced framework version.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    n_total integer;
    n_sup integer;
    n_part integer;
    n_fut integer;
    n_miss integer;
BEGIN
    -- Scoped to THIS catalogue's framework version, so the assertion is exact
    -- even in a test/QA database that already holds unrelated requirement rows
    -- under other version labels (observed: 89 such rows in a verification
    -- clone). An unscoped table count would raise a false alarm there.
    SELECT count(*) INTO n_total
      FROM public.disclosure_requirement_versions rv
      JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id
      JOIN public.disclosure_frameworks f ON f.id = fv.framework_id
     WHERE f.code = 'GHG_PROTOCOL'
       AND fv.version_label = 'Corporate Accounting and Reporting Standard (2004 revised edition)';
    IF n_total <> 18 THEN
        RAISE EXCEPTION
            'P17-K: governed capability catalogue incomplete (% of 18 requirement rows present on the evidenced framework version).', n_total;
    END IF;

    -- The rollup itself is asserted, not merely the row count: a catalogue of
    -- the right SIZE but the wrong MAPPING is the more dangerous failure, and
    -- it is invisible to a count. 4 / 6 / 3 / 2 is frozen (P17-DECISION-03
    -- §11.1) and non-upgrading (§11.3 `S3-2`).
    SELECT count(*) FILTER (WHERE rv.carbontally_capability = 'SUPPORTED'),
           count(*) FILTER (WHERE rv.carbontally_capability = 'PARTIALLY_SUPPORTED'),
           count(*) FILTER (WHERE rv.carbontally_capability = 'FUTURE'),
           count(*) FILTER (WHERE rv.carbontally_capability = 'MISSING_CAPABILITY')
      INTO n_sup, n_part, n_fut, n_miss
      FROM public.disclosure_requirement_versions rv
      JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id
      JOIN public.disclosure_frameworks f ON f.id = fv.framework_id
     WHERE f.code = 'GHG_PROTOCOL'
       AND fv.version_label = 'Corporate Accounting and Reporting Standard (2004 revised edition)'
       AND rv.requirement_code LIKE 'GP-S3-CAT-%';
    IF (n_sup, n_part, n_fut, n_miss) <> (4, 6, 3, 2) THEN
        RAISE EXCEPTION
            'P17-K: Scope 3 capability rollup is %/%/%/% but the frozen matrix requires 4/6/3/2 (P17-DECISION-03 §11.1).',
            n_sup, n_part, n_fut, n_miss;
    END IF;

    -- Scope 2: the market-based requirement must never be recorded as producible
    -- while no market-based engine exists (§8.3, §9.4 item 4, `SC-4`).
    IF EXISTS (
        SELECT 1
          FROM public.disclosure_requirement_versions rv
          JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id
          JOIN public.disclosure_frameworks f ON f.id = fv.framework_id
         WHERE f.code = 'GHG_PROTOCOL'
           AND fv.version_label = 'Corporate Accounting and Reporting Standard (2004 revised edition)'
           AND rv.requirement_code = 'GP-S2-MB'
           AND rv.carbontally_capability IN ('SUPPORTED', 'PARTIALLY_SUPPORTED')
    ) THEN
        RAISE EXCEPTION
            'P17-K: a market-based Scope 2 requirement was recorded with producible capability while no market-based engine exists (P17-DECISION-03 §8.3 / SC-4).';
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION CHECKLIST (P17-K)
--   [ ] 1 framework version row exists for GHG_PROTOCOL with the evidenced
--       label and NOWHERE an invented date/legal reference
--   [ ] exactly 18 requirement rows: GP-S1, GP-S2-LB, GP-S2-MB, GP-S3-CAT-01..15
--   [ ] every carbontally_capability value is one of the 7 governed values
--   [ ] every requirement_class value is one of the 8 governed values
--   [ ] NO 'NOT_APPLICABLE' requirement class and NO applicability vocabulary
--   [ ] NO Axis-A token ('PARTIAL' / 'DEFERRED' / 'NOT_IMPLEMENTED') appears as
--       a value in any column of either table, for these rows
--   [ ] NO new table / column / enum / CHECK / index / policy was created
--   [ ] NO 'organization_id' (or any tenant key) exists on these rows
--   [ ] the Scope 3 capability rollup derivable from the rows is 4 / 6 / 3 / 2
--   [ ] re-running this file inserts nothing (0 new rows)
--   [ ] every historical row and every other catalogue table is unchanged
-- ============================================================================

