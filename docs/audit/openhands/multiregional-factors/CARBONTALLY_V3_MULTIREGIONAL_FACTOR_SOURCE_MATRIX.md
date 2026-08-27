# CARBONTALLY V3 — MULTIREGIONAL EMISSION FACTOR SOURCE & COVERAGE RESEARCH

**Research only.** No CarbonTally code, schema, migrations, factor tables, imports, RLS, production data, commits or pushes were changed.

- Canonical baseline: `origin/main` `d4dcca1eb11f86bcae497815c8592d688a7e305f`
- Isolated clone: `/tmp/carbontally-v3-research`
- Access date: 2026-08-24
- `[C#]` repository evidence; `[S#]` source register evidence.
- This contains no emission-factor values and is not a production seed/import file.

## 1. Executive Summary

CarbonTally already has 7,029 managed DEFRA rows, 20 managed SEAI rows, and org-scoped Customer Custom Emission Factors. Existing conventions are `DEFRA-DESNZ`/`DEFRA-2025`/`GB` and `SEAI`/`SEAI-2025`/`IE`; they must be preserved, not rebuilt or re-imported as new capabilities. [C1][C2]

The major multinational gap is country-aware EU coverage beyond GB/IE, beginning with location-based electricity for Germany, France and other countries. No single verified EU source is a complete corporate factor library. Prioritize EEA electricity as a candidate, validate boundaries and years against national sources, then add scoped EU ETS/IPCC stationary candidates. For the US, prioritize EPA GHG Emission Factors Hub physical defaults and EPA eGRID location-based electricity; MOVES and WARM are models, not universal flat tables. [S5][S6][S12][S13][S14][S15][S17][S19][S20]

Spend-based support is later/P3 because the current direct-multiply contract does not explicitly encode currency, price year, inflation, economic sector or lifecycle boundary, and the current EPA spend download was not verified. [C1][C2][S21]

## 2. CarbonTally Existing Factor Capabilities

| Capability | Actual current state | Treatment |
|---|---|---|
| UK DEFRA/DESNZ | Global `emission_factors`; importer defaults `DEFRA-DESNZ`, `DEFRA-<year>`, `GB`; baseline 7,029 rows; 2025 flat workbook. | Existing P0: preserve/verify; no new DEFRA import. [C1][C2] |
| Ireland SEAI | Provider maps 28 workbook rows to 20 canonical factors, skips 8; `SEAI`, `SEAI-2025`, `IE`, year 2025; CO2-only semantics retained. | Existing P0: preserve/verify; no rebuild. [C1][C2] |
| Customer Custom Factors | Org-scoped `customer_factors`; draft/active/inactive/archived; versioned; active exact customer candidate precedes managed matching; current country check GB/IE. | Existing P0: preserve; do not replace. [C1][C2] |
| Mapping/resolution/calculation/evidence | CSV/Excel flow; `MatchRequest` has activity, country, year, unit, scope, organization; natural-key/exact/alias/keyword/fuzzy/optional semantic matching; immutable snapshots and evidence pointers. | Existing architecture; extend only by approved decision. [C1][C2] |

## 3. Current Factor Schema

Managed `EmissionFactor`: `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `factor_source`, `factor_set`, `country`, `provider_key`, `import_batch_id`, and natural key `(reporting_year, activity_type, country, unit, scope)`. `provider_key`, `provider_version`, `source_file`, checksum, status, active flag and rollback link are on `import_batches`. Customer factors additionally have organisation, name, source reference, category, methodology, effective dates, status, version, metadata and audit actors. [C1][C2]

The calculation engine checks exact unit equality and computes quantity × `co2e_multiplier`; snapshots retain factor kind, IDs, batch, year, methodology, algorithm version, content hash and source file/page/item. [C1][C2]

**Limitation:** managed uniqueness excludes source/set/methodology. Same-year/activity/country/unit/scope alternatives can collide or be overwritten. This is a **PRODUCT DECISION REQUIRED**, not an importer workaround.

## 4. Factor Resolution Architecture

`/api/v3/emissions/factors` supports year, country, scope, unit, source, set and provider filters. `/api/v3/emissions/calculate` supports explicit managed `factor_id`, active customer `customer_factor_id`, or matching. Current D-cf-5 is active exact customer factor first, then managed pipeline. [C1][C2]

Recommended policy: retain that current rule for an approved exact in-scope customer factor; if customer and regional factors are only plausible matches, return review/selection rather than silently choosing. Any change is **PRODUCT DECISION REQUIRED**.

## 5. UK Coverage

Existing DEFRA/DESNZ 2025 is the correct UK baseline. GOV.UK publishes condensed/full/flat files, methodology and change documents; the flat file is intended for automatic processing and the publication covers UK/international organisation reporting. [S1][S2]

The inspected 2025 workbook contains physical labels including `kWh`, `litres`, `kg`, `tonnes`, `km`, `tonne.km` and `passenger.km`. No obvious spend/currency label was found in workbook strings; this is not a formal DB audit. [C1]

Potential future gaps are verification only: batch/checksum links for legacy rows, source IDs/hierarchy in metadata, annual/historical releases, calorific basis, CO2 versus CO2e, and whether any spend rows exist. Do not assume DEFRA electricity is market-based. [S1][S2][S22]

## 6. Ireland Coverage

Existing SEAI coverage is the 2025/V1.7 workbook convention and canonical physical fuels/electricity. Provider code assigns Scope 1 to fuels and Scope 2 to electricity and deliberately preserves CO2-only semantics. The live SEAI page returned 403; current publication/licence details are **Source retrieval incomplete — requires manual verification**. [C1][C2][S4]

Current canonical coverage does not establish all Irish transport, waste, refrigerant, industrial/agriculture categories or market-based electricity. [S4][S22]

## 7. EU/EEA Coverage

No single verified EU source is a universal corporate factor set. The EEA electricity indicator is a country-level generation-intensity candidate, not automatically purchased-consumption, residual-mix or contractual market-based electricity. [S5][S22]

EMEP/EEA Guidebook/viewer is inventory guidance and selected factors; the viewer says it is incomplete and the chapter controls discrepancies. It is not a complete corporate CO2e library. [S6][S7]

EC Environmental Footprint/PEF/OEF and LCDN are the strongest EU-aligned direction for later lifecycle Scope 3/product data: primary data is preferred for controlled processes and EF-compliant secondary data for outside control. Retain dataset/process/reference-flow/geography/impact-method metadata; do not flatten lifecycle datasets into generic direct factors. [S9][S10][S27]

EU ETS MRR and IPCC defaults can support carefully scoped stationary fallbacks, but their intended uses are regulated-installation monitoring and national inventory methodology, not one universal EU corporate set. [S12][S13][S14]

| Category | Evidence-based finding | Priority |
|---|---|---|
| Electricity | EEA country-level generation candidate; national/contractual sources may be required. | P1 location-based |
| Fuels/stationary | EU ETS MRR, IPCC and national bases differ. | P1/P2 scoped |
| Transport | No single verified corporate EU table; mode/geography/load/boundary matter. | P2 |
| Waste | Treatment pathways and national assumptions differ; no complete universal table verified. | P2 |
| Refrigerants/F-gases | Substance and GWP vintage required; complete organisation-ready table not verified. | P2/P3 |
| Industrial/agriculture/land | Inventory methods exist, not one flat corporate library. | P3 |
| Scope 3 products/materials | EF/LCDN candidate, lifecycle-specific and licence-dependent. | P2/P3 separate capability |

UBA (Germany) and ADEME/Base Empreinte (France) are credible discovery candidates, but current downloads/licences were not verified. [S25][S26]

## 8. US Coverage

EPA describes the GHG Emission Factors Hub as transparent organisational defaults and publishes 2025 plus archived releases. The 2025 workbook contains distinct stationary/mobile/fuel/refrigerant/waste-related tables and relevant gas components; do not assume every row is pre-combined CO2e. [S15][S16]

EPA eGRID provides release-specific electricity rates, generation/resource data and geography; detailed data lists eGRID2023 rev2 and technical resources include methodology/electricity-use guidance. It is the leading US location-based electricity candidate. [S17][S18]

MOVES estimates mobile emissions at national, county and project level and needs scenario inputs; WARM models waste-management pathways. Preserve model version, geography, pathway and inputs rather than flattening generic factors. [S19][S20]

The EPA supply-chain guidance page was retrieved, but a current official EEIO/spend download was not verified; the prior candidate URL returned 404. **Source retrieval incomplete — requires manual verification.** [S21]

## 9. Electricity Factors

Maintain three distinct families: (1) location-based grid generation/intensity keyed by activity geography, year and release; (2) market-based supplier/contractual/residual-mix evidence; (3) on-site generation/export treatment. Use existing DEFRA for GB, SEAI for IE, EEA plus verified national sources for EU, and eGRID for US. Never infer market-based electricity from a grid average. Current fields fit simple location-based rows but not full contractual evidence or same-key parallel methods. **PRODUCT DECISION REQUIRED.** [S1][S4][S5][S17][S22]

## 10. Physical Activity Factors

Physical factors remain the first-class path: `kWh`, litres, kg, tonnes, m3, km, passenger.km and tonne.km. Exact unit equality is enforced; do not silently convert units or calorific bases. Store source basis, unit, scope, activity country, year, source/set and batch checksum. Transport requires mode/vehicle/fuel/geography/load/boundary; waste requires material/pathway; refrigerants require substance/GWP vintage. [C1][C2]

## 11. Spend-Based Factors

Spend factors need currency, price year, deflator/inflation basis, economic-sector classification, purchaser geography and lifecycle boundary. A generic `unit` string and direct multiplication do not supply those semantics. Recommend **later/P3**, after a Product Owner decision, licensed source recovery and separate mapping/review. Do not mix `GBP spent`, `EUR spent` and `USD spent` with physical factors. [C1][C2][S21]

## 12. Scope 1

Use existing DEFRA/SEAI fuels, EPA Hub, scoped EU ETS/IPCC defaults and substance/process-specific refrigerant, fugitive and industrial candidates. Scope is row/boundary-specific; source presence does not universally make a factor Scope 1. [S1][S2][S4][S12][S13][S15]

## 13. Scope 2

Purchased/acquired electricity, steam, heat and cooling need location-based and market-based treatment kept separate. Existing DEFRA/SEAI electricity must not be relabelled market-based; EEA/eGRID require geography/year/boundary validation. [S5][S17][S22]

## 14. Scope 3

Consider purchased goods/capital goods, fuel-and-energy-related activities, upstream/downstream transport, business travel, commuting, waste, leased assets, use and end-of-life, supplier-specific and lifecycle factors. Use GHG Protocol for category/boundary method and licensed EF/LCDN or other datasets for factors; its terms restrict commercial copying/extraction. [S23][S24]

## 15. Licensing

| Source | Result |
|---|---|
| UK GOV/DESNZ | OGL v3 permits commercial exploitation, adaptation and distribution with attribution; exclusions/third-party rights apply. Suitable in principle. [S1][S3] |
| EEA | CC-BY generally for EEA-owned material; item-specific data/third-party terms prevail. Suitable in principle after item check. [S8] |
| EC/JRC | CC BY 4.0 site policy is not blanket permission for each EF/LCDN dataset. Dataset check required. [S9][S10][S11][S27] |
| SEAI | **LICENSING NOT YET VERIFIED.** [S4] |
| EPA | **NOT VERIFIED AS DATASET-WIDE**; check each workbook/model/disclaimer. [S15][S17][S19][S20] |
| IPCC | **LICENSING NOT YET VERIFIED** for factor/database reuse. [S13][S14] |
| GHG Protocol | Commercial copying/extraction restricted by terms; methodology reference only. [S24] |
| UBA/ADEME | **LICENSING NOT YET VERIFIED.** [S25][S26] |

Retain attribution text, exact URL, filename, release and checksum for approved imports. No credentials/customer data were reproduced.

## 16. Provenance

Use existing chain `factor → import_batch → provider/version/source_file/source_checksum/year/status/active/rollback → calculation_snapshot → source file/page/item/content hash`. Map authority to `factor_source`, release to `factor_set`, applicability to `country`, source unit to `unit`, intended accounting use to `scope`, and release year to `reporting_year`. Provider-specific IDs/URLs/methodology/attribution remain in provider artifacts/metadata unless an approved schema change makes them first-class. [C1][C2]

## 17. Versioning

Each release must be immutable metadata: reporting year, publication/release date, provider version, exact URL/filename, SHA-256, source ID, GWP/method basis, geographic level and import status. Existing batches support inactive history and rollback. One active batch per provider/year and current upsert behavior need review for parallel methods/revisions. **PRODUCT DECISION REQUIRED.** [C1][C2]

## 18. Multinational Customer Example

For one organisation with UK, Ireland, Germany, France and US sites: UK electricity resolves to existing GB/DEFRA location-based coverage; Irish electricity to existing IE/SEAI with CO2-only disclosure; German/French electricity to validated EEA/national country candidates; US electricity to eGRID geography. Fuel uses activity country, physical unit and calorific/CO2 basis: existing GB/IE, scoped EU/national DE/FR, EPA Hub US. Transport requires mode/fuel/geography/load/boundary and may use MOVES or EF/model data. Organisation headquarters must not override activity country. [C1][C2][S5][S17][S19]

## 19. Source Comparison Matrix

| Region | Source | Authority | Category/geography | Unit | Scope | Year/method | Licensing | CarbonTally fit |
|---|---|---|---|---|---|---|---|---|
| UK | DEFRA/DESNZ | UK Government | fuels, stationary/mobile, electricity, published families / UK | source physical | row-specific corporate | 2025/method paper | OGL v3 in principle | Existing P0 |
| Ireland | SEAI | Irish agency | fuels/electricity / Ireland | source physical | Scope 1/2 in provider; CO2-only | 2025/V1.7/workbook | Not verified | Existing P0 |
| EU/EEA | EEA electricity indicator | EU agency | generation intensity / Europe-country | published intensity | Scope 2 location candidate | release-specific/EEA | CC-BY generally; data check | P1 |
| EU/EEA | EMEP/EEA | EEA/EMEP | inventory factors / Europe-national | source-specific | scope mapping needed | 2023/inventory | data check | P3 scoped |
| EU/EEA | EU ETS MRR | EU law | installation fuels/process / EU ETS | legal-annex | regulated Scope 1 context | regulation/amendments | extraction check | P1/P2 scoped |
| EU/EEA | EC EF/LCDN | EC/JRC | lifecycle products/materials / dataset | reference-flow | mainly Scope 3/LCA | dataset release/PEF-OEF | dataset check | P2/P3 separate |
| EU/EEA | IPCC | scientific institution | fuels/industry/agriculture/land/waste / defaults | source-specific | scope mapping | 2006/2019/inventory | not verified | P2/P3 fallback |
| US | EPA Hub | US EPA | stationary/mobile/fuel/refrigerant/waste / US | source physical/gas components | row-specific | 2025/EPA notes | artifact check | P1 |
| US | eGRID | US EPA | electricity / plant-state-subregion-national | electricity intensity | Scope 2 location | release/method | workbook check | P1 |
| US | MOVES | US EPA | mobile model / national-county-project | scenario output | Scope 1/3 boundary | model release | not verified | P2 model |
| US | WARM | US EPA | waste pathways / US assumptions | mass/pathway output | Scope 3 waste | model release | not verified | P2 model |
| DE | UBA candidate | national agency | national factor candidate / Germany | not verified | row-specific | not verified | not verified | P2 discovery |
| FR | ADEME candidate | national agency | carbon/LCA candidate / France | not verified | row-specific | release-specific | not verified | P2 discovery |

## 20. Coverage Gaps

1. Approved DE/FR/other EU country electricity beyond GB/IE.
2. Separate market-based electricity evidence/method.
3. US eGRID provider/geography.
4. US transport/waste model-backed coverage.
5. EU transport, waste, refrigerant, industrial, agriculture and broad Scope 3 families.
6. Spend source, currency/price basis and licence.
7. Same-key alternative source/set/method coexistence.
8. Generic source URL/identifier/methodology beyond provider metadata.
9. Customer-factor geography beyond current GB/IE.
10. Parallel historical releases under one-active-batch/upsert behavior.

## 21. Recommended Factor Roadmap

- **Phase 1 / P0:** preserve/verify DEFRA, SEAI and custom factors; batch links/checksums; year/country/unit/scope; CO2/CO2e presentation; activity-country and exact-unit tests.
- **Phase 2 / P1/P2:** EEA/national country-level location-based electricity; scoped EU ETS/IPCC stationary candidates; DE/FR licence review; separate category backlog.
- **Phase 3 / P1/P2:** EPA Hub physical defaults and eGRID; then MOVES/WARM models with scenario provenance.
- **Phase 4 / P2/P3:** EC EF/LCDN lifecycle Scope 3, supplier-specific factors and separately licensed EEIO/spend.

## 22. Product Decisions Required

Customer-vs-regional precedence; mandatory activity country; same-key alternative uniqueness; Scope 2 location/market evidence; SEAI CO2-only presentation; EF/LCDN product boundary; spend currencies/price years/boundaries; EU national prioritisation; licence/attribution UX.

## 23. Source Register

| ID | Organisation/title/use | URL and verification |
|---|---|---|
| C1 | CarbonTally canonical origin/main at d4dcca1eb11f86bcae497815c8592d688a7e305f | https://github.com/shomonrobie/CarbonTally/tree/d4dcca1eb11f86bcae497815c8592d688a7e305f (accessed 2026-08-24) |
| C2 | CarbonTally runtime inspection: backend/domain/factor.py, customer_factor.py, matching.py; backend/engines/factor_matching.py; backend/api/v3_emissions.py; backend/data/emission_factors.py; import/customer-factor migrations; src/providers/defra and seai | Repository evidence (accessed 2026-08-24) |
| S1 | UK Government/DESNZ, Greenhouse gas reporting: conversion factors 2025; 2025 files and methodology | https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025 (accessed 2026-08-24) |
| S2 | UK Government/DESNZ, Conversion factors 2025: methodology | https://assets.publishing.service.gov.uk/media/6846b0870392ed9b784c0187/2025-GHG-CF-methodology-paper.pdf (accessed 2026-08-24) |
| S3 | UK National Archives, Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ (accessed 2026-08-24) |
| S4 | SEAI, Conversion factors publication area; retrieval returned 403, so current release/licence needs manual verification | https://www.seai.ie/data-and-insights/seai-statistics/conversion-factors (accessed 2026-08-24) |
| S5 | EEA, Greenhouse gas emission intensity of electricity generation in Europe | https://climate-energy.eea.europa.eu/topics/climate-change-mitigation/greenhouse-gas-emissions-inventory/indicators/greenhouse-gas-emission-intensity-of-electricity-generation-in-europe (accessed 2026-08-24) |
| S6 | EEA/EMEP, EMEP/EEA air pollutant emission inventory guidebook 2023; published 2023-10-02 | https://www.eea.europa.eu/en/analysis/publications/emep-eea-guidebook-2023 (accessed 2026-08-24) |
| S7 | EEA, EMEP/EEA emission factor data viewer; selected factors only | https://efdb.apps.eea.europa.eu/ (accessed 2026-08-24) |
| S8 | EEA, Legal notice; CC-BY generally for EEA-owned material, item-specific terms prevail | https://www.eea.europa.eu/en/legal-notice (accessed 2026-08-24) |
| S9 | European Commission, Environmental Footprint Methods | https://green-forum.ec.europa.eu/green-business/environmental-footprint-methods_en (accessed 2026-08-24) |
| S10 | European Commission, Data for EF methods; primary data and EF-compliant secondary data hierarchy | https://green-forum.ec.europa.eu/green-business/environmental-footprint-methods/data-ef-methods_en (accessed 2026-08-24) |
| S11 | European Commission, Legal notice; CC BY 4.0 generally for EU-owned site content, third-party rights excluded | https://commission.europa.eu/legal-notice_en (accessed 2026-08-24) |
| S12 | European Union, Commission Regulation (EU) 2018/2066, Monitoring and Reporting Regulation | https://eur-lex.europa.eu/eli/reg/2018/2066/oj (accessed 2026-08-24) |
| S13 | IPCC-NGGIP, 2006 IPCC Guidelines | https://www.ipcc-nggip.iges.or.jp/public/2006gl/ (accessed 2026-08-24) |
| S14 | IPCC-NGGIP, 2019 Refinement | https://www.ipcc-nggip.iges.or.jp/public/2019rf/ (accessed 2026-08-24) |
| S15 | US EPA, GHG Emission Factors Hub; 2025 workbook/PDF; PDF last modified 2025-01-15 | https://www.epa.gov/climateleadership/ghg-emission-factors-hub (accessed 2026-08-24) |
| S16 | US EPA, 2025 GHG Emission Factors Hub workbook | https://www.epa.gov/system/files/other-files/2025-01/ghg-emission-factors-hub-2025.xlsx (accessed 2026-08-24) |
| S17 | US EPA, eGRID detailed data; eGRID2023 rev2 listed | https://www.epa.gov/egrid/detailed-data (accessed 2026-08-24) |
| S18 | US EPA, eGRID technical resources and electricity-use guidance | https://www.epa.gov/egrid/technical-resources (accessed 2026-08-24) |
| S19 | US EPA, MOVES mobile-source emissions model | https://www.epa.gov/moves (accessed 2026-08-24) |
| S20 | US EPA, Waste Reduction Model (WARM) | https://www.epa.gov/waste-reduction-model (accessed 2026-08-24) |
| S21 | US EPA, Supply Chain Guidance; current spend-factor download not verified; previous candidate URL returned 404 | https://www.epa.gov/climateleadership/supply-chain-guidance (accessed 2026-08-24) |
| S22 | GHG Protocol, Scope 2 Guidance; location/market distinction | https://ghgprotocol.org/scope-2-guidance (accessed 2026-08-24) |
| S23 | GHG Protocol, Scope 3 Calculation Guidance | https://ghgprotocol.org/scope-3-calculation-guidance-2 (accessed 2026-08-24) |
| S24 | GHG Protocol, Terms of Use; commercial copying/extraction restrictions | https://ghgprotocol.org/terms-use (accessed 2026-08-24) |
| S25 | German Environment Agency UBA candidate; current page retrieval incomplete — requires manual verification | https://www.umweltbundesamt.de/en/topics/climate-energy/greenhouse-gas-emissions/emission-factors (accessed 2026-08-24) |
| S26 | ADEME Base Empreinte candidate; page returned 403 — manual verification required | https://base-empreinte.ademe.fr/ (accessed 2026-08-24) |
| S27 | European Commission/JRC Life Cycle Data Network / EPLCA | https://eplca.jrc.ec.europa.eu/LCDN/index.html (accessed 2026-08-24) |

Unverified/incomplete retrieval or licensing must be manually checked; do not infer permission or coverage.
