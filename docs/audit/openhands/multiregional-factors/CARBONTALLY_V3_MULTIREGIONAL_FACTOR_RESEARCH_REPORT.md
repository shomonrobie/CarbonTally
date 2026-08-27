# CARBONTALLY V3 — MULTIREGIONAL FACTOR RESEARCH REPORT

**Research-only completion report.** Accessed 2026-08-24. Canonical baseline `d4dcca1eb11f86bcae497815c8592d688a7e305f`. No CarbonTally code, schema, migration, RLS, factor data, import, production data, commit or push changed.

## What was researched

An isolated read-only clone was inspected before primary-source research. Actual managed factor, customer factor, import batch, matching, calculation, API, snapshot, migration, provider, test and provenance terminology was recorded. UK, Ireland, EU/EEA and US official sources were assessed for coverage, methodology, units, geography, scopes, versioning and licensing. This report and its JSON are candidate metadata, not factor values or seed data.

## Existing coverage

CarbonTally already has DEFRA/DESNZ (7,029 baseline managed rows), Irish/SEAI (20 canonical rows from 28 source rows; eight skipped) and org-scoped Customer Custom Emission Factors. Existing conventions are DEFRA-DESNZ/DEFRA-2025/GB and SEAI/SEAI-2025/IE. Preserve them; do not rebuild. [C1][C2]

## Main findings

- **UK:** DEFRA/DESNZ 2025 is the existing baseline. Official flat, full, condensed, methodology and changes files exist; OGL v3 is suitable in principle with attribution. Future work is verification, not re-import. [S1][S2][S3]
- **Ireland:** SEAI is existing current fuel/electricity coverage and intentionally preserves CO2-only semantics. Live page retrieval returned 403; current publication/licence details are **Source retrieval incomplete — requires manual verification**. [S4]
- **EU/EEA:** no universal corporate factor set was verified. EEA electricity is the best starting candidate for country-level location-based electricity. EMEP/EEA is inventory guidance/selected factors. EC EF/LCDN is better for later lifecycle Scope 3 and must remain dataset-specific. EU ETS/IPCC are scoped defaults. [S5][S6][S7][S9][S10][S12][S13][S14][S27]
- **US:** prioritize EPA Hub physical defaults and eGRID location-based electricity. MOVES and WARM are scenario/pathway models. EPA spend-factor retrieval is incomplete. [S15][S17][S18][S19][S20][S21]

## Compatibility with actual CarbonTally architecture

Managed fields are `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `factor_source`, `factor_set`, `country`, `provider_key`, `import_batch_id` and natural key `(reporting_year, activity_type, country, unit, scope)`. Batch fields provide provider/version/source file/checksum/status/active/rollback. Exact unit equality is enforced. Current customer factor checks allow GB/IE only. [C1][C2]

The fields fit physical location-based rows, but not full market-based contractual evidence or spend currency/price semantics. Natural-key uniqueness excludes source/set/methodology, so same-key alternatives can overwrite/collide. **PRODUCT DECISION REQUIRED.**

## Electricity

Keep location-based grid, market-based supplier/contract/residual mix and on-site/export treatment separate. Use existing DEFRA GB, SEAI IE, validated EEA/national EU and eGRID US. Never infer market-based from an average grid factor. [S5][S17][S22]

## Physical and spend

Physical factors are current first-class: kWh, litres, kg, tonnes, m3, km, passenger.km and tonne.km. Preserve exact unit, basis, scope, country, year, source/set and checksum; do not silently convert. Spend is later/P3 after Product Owner approval, a licensed source, currency/price-year/sector/boundary rules and separate review. [C1][C2][S21]

## Scopes

Scope 1: existing fuels plus EPA Hub and scoped EU ETS/IPCC/process candidates. Scope 2: electricity/steam/heat/cooling with location and market distinct. Scope 3: purchased goods/capital goods, fuel-and-energy-related, transport, travel, commuting, waste, leased assets, use/end-of-life, supplier-specific and lifecycle factors. GHG Protocol is methodology only; its terms restrict commercial copying/extraction. [S22][S23][S24]

## Licensing

UK OGL and EEA/Commission-owned content are commercially reusable in principle with attribution and item-level checks. SEAI, EPA artifact/model terms, IPCC factor data, UBA, ADEME and individual EF/LCDN datasets remain **LICENSING NOT YET VERIFIED** where exact terms were not established. GHG Protocol terms restrict commercial copying/extraction. [S3][S8][S11][S13][S15][S24][S25][S26][S27]

## Multinational example

For UK, IE, DE, FR and US sites: UK electricity uses existing GB/DEFRA location-based coverage; IE uses existing IE/SEAI with CO2-only disclosure; DE/FR require EEA/national country candidates; US uses eGRID geography. Fuel uses activity country, unit and calorific/CO2 basis. Transport requires mode, fuel, geography, load and boundary; it does not resolve from organisation country alone. [C1][C2][S5][S17][S19]

## Next Cline task and prohibitions

Next: a QA-first, no-import plan for one EU/EEA location-based electricity release, Germany and France first; verify source/boundary/country/year/licence/attribution/identifier/checksum/coexistence before importing. Then assess EPA Hub/eGRID.

Cline must not re-import/rebuild DEFRA, SEAI or custom factors; change schema/migrations/RLS/calculation/snapshots; import this JSON; add unsupported values; merge physical and spend; collapse location and market electricity; overwrite same-key alternatives; or modify production data.

## Product Owner decisions

Approve customer-vs-regional precedence; activity-country requirement; same-key alternatives; Scope 2 methods/evidence; SEAI CO2-only reporting; EF/LCDN boundary; spend support/currencies/price years; EU national priorities; and licence/attribution UX.

## Explicit answers

1. Existing: DEFRA/DESNZ, Irish/SEAI and Customer Custom Emission Factors. [C1][C2]
2. Missing EU: DE/FR/other country electricity plus broad transport/waste/refrigerant/industry/agriculture/Scope 3.
3. Prioritize EEA country-level location-based electricity, then scoped EU ETS/IPCC stationary and verified national sources.
4. Yes, country-specific EU factors where grid, boundary, regulation, waste pathway or method differs; avoid redundant 27 imports.
5. US: EPA Hub physical defaults and EPA eGRID; MOVES/WARM later as models.
6. Electricity: distinct location-based, market-based and on-site/export families by activity geography/year.
7. Commercial in principle: UK OGL and EEA/Commission-owned material with attribution and item checks.
8. Uncertain: SEAI, EPA dataset-wide terms, IPCC data, UBA, ADEME, EF/LCDN and EPA spend candidate.
9. Spend later/P3, not now.
10. Scope 3: purchased goods/capital goods, fuel/energy, transport, travel, commuting, waste, leased assets, use/end-of-life, supplier/lifecycle.
11. Use existing source/set/year/country/unit/scope/provider/batch/snapshot fields; source IDs/URLs/methodology in provider metadata unless approved schema change.
12. Next import task: QA-first EEA location electricity plan for DE/FR; no automatic import.
13. Do not change existing providers/custom factors/schema/migrations/RLS/production data/engine semantics.
14. PO decisions: precedence, country, alternative uniqueness, Scope 2, CO2-only, lifecycle boundary, spend, EU priority, licensing UX.

See the matrix and JSON source register for URLs and access dates.
