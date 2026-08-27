# CARBONTALLY V3 — UK LAUNCH EMISSION FACTOR COVERAGE GAP RESEARCH

**Research-only artifact.** No CarbonTally code, database, schema, migration, RLS, factor table, production data, import, commit or push was changed.

- Canonical baseline inspected in an isolated read-only clone: `origin/main` `d4dcca1eb11f86bcae497815c8592d688a7e305f`
- Research date: 2026-08-24
- `[C#]` = CarbonTally repository evidence; `[S#]` = official source register evidence.
- This is not a factor seed/import specification and contains no emission-factor values.
- For blocked or unavailable sources: **Source retrieval incomplete — requires manual verification**.

## 1. Executive conclusion

**For a UK-only launch reporting 2025 activity, current CarbonTally DEFRA coverage is broadly sufficient for common UK activity-based requirements. For a launch processing 2026 activity, CarbonTally should verify and adopt the 2026 DEFRA release before treating its UK factors as current-year launch coverage.** This is a version refresh of an existing provider, not a new factor source.

The current 2025 import covers 7,029 numeric rows across fuels, bioenergy, refrigerants/process gases, UK electricity, heat/steam, water, materials, waste, passenger/delivery/managed vehicles, business travel, freight, hotel stays, homeworking, WTT, T&D, EV and SECR-specific categories. It has Scope 1 (2,531), Scope 2 (352), Scope 3 (4,090) and Outside of Scopes (56) rows, all `DEFRA-DESNZ` / `DEFRA-2025` / `GB`. [C1][C2][C3]

The 2026 revised flat file has 7,035 numeric factor rows: 7,029 IDs common with the current 2025 import plus six new IDs. Those additions are one `Material use` wood closed-loop row and five `Waste disposal` rows for household residual and commercial/industrial waste treatment routes. The 2026 full set also contains an `Overseas electricity` worksheet that is not present in the current flat-file import; that is a multinational/full-set gap, not a UK-only launch blocker. [S1][S3][S4][S5]

No separate UK factor provider is required for common launch activity data. The important pre-launch action is a 2026 DEFRA refresh/verification gate if 2026 reporting is in scope, plus clear treatment of the six 2026 flat additions, full-set-only overseas electricity, historical years and licensing/provenance.

## 2. Existing CarbonTally capabilities (verified)

| Capability | Verified current state | UK-launch treatment |
|---|---|---|
| DEFRA/DESNZ | 7,029 imported rows; `reporting_year=2025`, `factor_source=DEFRA-DESNZ`, `factor_set=DEFRA-2025`, `country=GB`; provider `defra`; batch/version pattern exists. | Existing P0; preserve, verify, and refresh for 2026 if needed. Do not rebuild. [C1][C2][C3] |
| Irish/SEAI | 20 canonical rows from 28 source rows, eight skipped; `SEAI` / `SEAI-2025` / `IE`; provider code retains CO2-only semantics. | Existing capability; irrelevant to UK-only factor gap except overseas IE operations. [C1][C2] |
| Customer Custom Factors | Org-scoped `customer_factors`, lifecycle draft/active/inactive/archived, version and metadata; current country check only GB/IE. | Existing fallback for customer-specific evidence; not a substitute for common DEFRA families. [C1][C2] |
| Matching/calculation | `MatchRequest` includes activity, country, year, unit, scope and organisation; active exact customer factor first; exact unit equality; quantity × `co2e_multiplier`; immutable snapshots/evidence. | Existing architecture fits physical UK factors. [C1][C2] |

## 3. Current CarbonTally factor representation

Managed `EmissionFactor` uses `id`, `reporting_year`, `activity_type`, `co2e_multiplier`, `unit`, `scope`, `factor_source`, `factor_set`, `country`, `provider_key`, `import_batch_id` and natural key `(reporting_year, activity_type, country, unit, scope)`. Batch provenance carries provider version, source file, checksum, status, active flag and rollback. Customer factors additionally carry organisation, name, source reference, methodology, status, version, metadata and effective dates. [C1][C2]

Current DEFRA mapping reads only the 2025 flat workbook’s `Factors by Category` data sheet with columns ID, Scope, Level 1–4, Column Text, UOM, GHG/Unit and `GHG Conversion Factor 2025`; factor rows with no numeric factor are skipped. The current generated import reports 8,742 parsed rows, 1,711 no-factor skips and 7,029 imported rows. [C3]

The existing factor contract is physically oriented and compatible with UK activity data. It does not explicitly distinguish currency/price basis for spend factors, or all location/market electricity evidence. Managed natural-key uniqueness excludes source, factor set and methodology, so competing same-key methods require Product Owner/schema approval rather than an importer workaround. [C1][C2]

## 4. DEFRA 2025 current coverage

The current import’s 32 Level-1 activity families are:

`Freighting goods`; `Managed assets- vehicles`; `Business travel- land`; `Delivery vehicles`; `Passenger vehicles`; `Fuels`; `SECR kWh pass & delivery vehs`; `Refrigerant & other`; `WTT- delivery vehs & freight`; `UK electricity for EVs`; `UK electricity T&D for EVs`; `WTT- pass vehs & travel- land`; `Waste disposal`; `WTT- fuels`; `Business travel- air`; `Material use`; `SECR kWh UK electricity for EVs`; `Outside of scopes`; `Bioenergy`; `WTT- bioenergy`; `Hotel stay`; `WTT- business travel- air`; `Business travel- sea`; `Heat and steam`; `Transmission and distribution`; `UK electricity`; `Managed assets- electricity`; `WTT- heat and steam`; `WTT- business travel- sea`; `Homeworking`; `WTT- UK electricity`; `Water supply`; and `Water treatment`. [C3]

Units in the imported rows are `km`, `miles`, `tonne.km`, `kg`, `tonnes`, `passenger.km`, `kWh (Net CV)`, `kWh (Gross CV)`, `litres`, `kWh`, `GJ`, `Room per night`, `cubic metres`, `per FTE Working Hour` and `million litres`. No spend/currency unit was found in the imported 2025 row metadata. [C3]

This coverage supports common UK offices, warehouses, retail, hospitality, professional services, logistics/fleet, property and many manufacturing use cases. It does not mean every customer-specific process, product, supplier, agricultural activity or industrial process has a suitable default.

## 5. DEFRA 2026 versus current CarbonTally data

### 5.1 Which year is currently used?

CarbonTally currently uses the 2025 DEFRA flat-format workbook and creates `DEFRA-2025` rows with reporting year 2025. The current 2026 GOV.UK publication is updated 31 July 2026 and its revised flat file is explicitly updated July 2026. [C1][C3][S1][S4]

### 5.2 Flat-file comparison

| Comparison | Result |
|---|---|
| 2025 current CarbonTally flat import | 7,029 numeric rows; 7,029 unique IDs; Scope 1 2,531, Scope 2 352, Scope 3 4,090, Outside of Scopes 56. [C3] |
| 2026 revised flat file | 7,035 numeric rows; same broad Level-1 families; six IDs not in the 2025 imported ID set. [S4] |
| Common IDs | 7,029. [C3][S4] |
| 2026-only rows | One `Material use` / wood / closed-loop row; five `Waste disposal` rows: household residual waste open-loop, closed-loop and anaerobic digestion; commercial and industrial waste closed-loop and anaerobic digestion. [S3][S4] |
| 2025-only IDs | None in the numeric flat-file comparison. [C3][S4] |

The six additions are not evidence of a missing UK-wide factor family. They are narrow 2026 coverage additions within already imported `Material use` and `Waste disposal` families. The 2026 major-changes report says no major methodological change for those sections, while the methodology describes alignment with GHG Protocol Scope 3 treatment and pathway limitations. [S2][S3]

### 5.3 2026 changes that matter operationally

- UK electricity methodology changed materially; the methodology says 2026 uses data one year before publication whereas the previous approach used a two-year lag, and therefore there is no 2024 data year. [S2]
- 2026 major changes include corrected/changed refrigerant blend treatment for R-511A, passenger/van/HGV/PHEV/BEV factors and electricity-related factors. [S3]
- The 2026 revised flat file corrected cases where unavailable WTT hybrid/CNG/LPG car and certain hotel values had been reported as zero instead of blank. [S4]
- The methodology uses revised 2021 Carbon Accounting Workbook inputs for water supply/treatment; the changes report does not label water as a major change, but a year refresh should still be verified. [S2][S3]
- Fuels, heat/steam, WTT fuels, business-travel categories, hotel stay, homeworking and many other categories are shown as having no major changes in the changes report; this does not remove the need to use the correct reporting year. [S3]

### 5.4 Full-set-only coverage

The 2026 full set contains an `Overseas electricity` worksheet. The current 2025 flat import contains no `Overseas` rows and the flat-file Level-1 list does not include that worksheet. The full set also includes explanatory/index/reference tabs not intended as direct factor rows. [C3][S5]

The methodology says overseas electricity/WTT data have changed in availability and points users toward IEA data for some overseas electricity/T&D/WTT needs; source and commercial terms must be checked. This is useful for UK organisations with overseas sites, but it is not necessary for UK activity at a UK-only launch. [S2][S5][S14]

### 5.5 Is 2026 required before launch?

- **If launch supports 2025 reporting periods only:** no; current 2025 DEFRA is the matching vintage, subject to existing provenance/QA.
- **If launch supports UK activity occurring in 2026:** yes, a 2026 DEFRA verification/import release should be a P0 launch gate. Calling 2025 rows “current 2026 factors” would be incorrect.
- **If the product supports multiple years:** retain 2025 and 2026 as separate reporting-year/factor-set vintages and keep historical snapshots reproducible. The official collection states that a new set is published annually and historical releases are available. [S1][S6]

This is not a recommendation to add a new source provider; it is a required current-year version decision.

## 6. UK customer use cases

| UK customer/use case | Common factor needs | DEFRA sufficient for common activity data? | Additional source at launch? | Custom/specialist boundary |
|---|---|---|---|---|
| Office/professional services | Mains electricity, gas, heat/steam, water, commuting, business travel, homeworking, waste | **Yes.** [C3][S1] | No | Supplier-specific electricity, travel or purchased-goods evidence may use Customer Custom Factors/primary data. |
| Warehouse/property | Electricity, fuels, refrigerants, water, waste, leased/managed assets, fleet | **Yes for common activities.** [C3][S2] | No | Building-specific HVAC/refrigerant or landlord factors may be custom. |
| Retail | Electricity, refrigerants, fuels, water, waste, materials, freight, employee travel | **Yes for common activities.** [C3][S1] | No | Product/material LCA and supplier-specific factors are later Scope 3 needs. |
| Hospitality | Electricity, fuels, water/treatment, waste, refrigerants, materials, hotel/business travel | **Yes for common activity data.** Hotel stay is present for staff travel. [C3][S2] | No | Hotel-stay underlying third-party rights and customer-specific hotel data need verification. |
| Logistics/fleet/transport | Fuels, passenger/delivery vehicles, EV electricity/SECR kWh, freight, WTT/T&D | **Yes for common UK fleet/freight activity data.** [C3][S2] | No | Telematics, unusual vehicles, leased-asset boundary or supplier-specific freight may be custom. |
| Manufacturing | Stationary fuels, electricity, heat/steam, refrigerants/process gases, water, waste, materials, owned fleet | **Mostly yes for listed activity families.** [C3][S2] | No general source | Sector/process-specific gases, feedstocks, cement/metal process chemistry or product LCA may need a specialist/custom factor. |
| Construction | Fuels, vehicles, electricity, materials, freight, waste, water | **Yes for common operational activity data.** [C3][S2] | No general source | Project/product embodied-carbon datasets and EPD/LCA sources are later specialist Scope 3. |
| Agriculture/land | Fuel, electricity, some waste/material activity | **Not complete for agriculture/land/livestock.** [S2][S6] | Not for ordinary UK launch | Specialist agricultural/land factors are P3 unless target customers require them; customer factors can cover evidenced supplier/process factors. |
| Specialised industrial processes | Refrigerants and “other” gases are present; process-specific coverage is row-dependent | **Not universally.** [S2][C3] | Not general launch source | Require verified process-specific source or Customer Custom Factor with evidence. |

The conclusion is not that DEFRA covers every emissions question; it is that no second general UK provider is justified for the common UK launch workload. [S1][S2][S6]

## 7. SECR

### Legal requirement

SECR applicability depends on organisation type and statutory thresholds; this report is not legal advice. GOV.UK guidance states that UK quoted companies report global energy use and GHG emissions and that large unquoted UK companies and LLPs have annual energy/GHG disclosure requirements. [S8]

### Official guidance

The UK company-reporting conversion-factor collection states that its factors are relevant to the Environmental Reporting Guidelines, including SECR, and are based on activity data such as fuel volume, purchased electricity kWh or distance travelled. [S6]

### Common SECR activity coverage

For common SECR data, CarbonTally’s current DEFRA set covers stationary and transport fuels, UK electricity, heat/steam, vehicle/fleet energy conversions, and Scope 1/2/3 labels. The 2026 methodology states that most SECR reporters need combustion of fuel, operation of facilities, and purchased electricity/heat/steam/cooling; energy-use reporting is distinct from emissions reporting. [C3][S2][S8]

### Common practice versus product opportunity

- **Common practice:** utility bills/meters, fuel invoices, fleet mileage/fuel, electricity kWh, heat/steam and documented activity evidence.
- **Product opportunity:** SECR-specific data completeness checks, intensity-ratio workflow, evidence collection, year/vintage selection, review/QC and report export.
- **Not a factor gap:** a SECR workflow opportunity does not justify a new factor provider when DEFRA already supplies the common activity factors.

## 8. Scope 1, 2 and 3

### Scope 1

DEFRA is sufficient for common UK combustion fuels, bioenergy treatment, company-owned/controlled passenger and delivery vehicles, and refrigerant/process-gas rows where the customer’s substance/process matches a published row. Specialised industrial chemistry, agriculture/livestock and unusual gases may require a verified specialist source or custom factor. [S1][S2][C3]

### Scope 2

DEFRA is sufficient for common UK location-based electricity and heat/steam activity data. 2026 UK electricity changes make year selection important. Market-based electricity claims, supplier contracts, certificates and residual mix must not be silently inferred from the location-based UK grid row; use separately evidenced customer/provider data under the Scope 2 method. [S2][S6][S11]

### Scope 3

The current import already contains substantial activity-based Scope 3 coverage: WTT fuels/electricity/T&D, business travel air/sea/land, freight, managed assets, waste, material use, hotel stay, homeworking and commuting/vehicle-related categories. [C3]

A separate Scope 3 factor database is **not required at UK launch** for these common physical categories. Additional Scope 3 data is useful later for purchased goods/services, capital goods, supplier-specific product factors, detailed lifecycle assessment and spend-based screening. Those can appropriately use primary data, supplier-provided data or Customer Custom Factors when supported by evidence; they should not be fabricated or conflated with DEFRA defaults. [S2][S6][S12]

## 9. Spend-based factors

The GOV.UK collection explicitly distinguishes the company-reporting conversion factors from Defra spend-based emissions multipliers. The spend multipliers are published with the UK carbon-footprint statistics and are intended primarily to compare carbon intensities of categories of final UK demand, though the collection says they can provide an initial supply-chain assessment where activity data is unavailable. [S6][S9]

They are therefore not a replacement for DEFRA activity factors. A spend factor needs currency, price/reference year, economic-sector classification, geography, boundary, lifecycle basis and methodology metadata. The current CarbonTally `unit`/direct-multiply contract does not make those semantics explicit. [C1][C2]

**Launch recommendation: do not support spend-based factors as a general launch feature (P3).** They are a product opportunity, not a UK launch factor gap. If later approved, maintain a separate spend family and require currency/price-year/sector/boundary/source/version evidence. The official 1997–2023 multiplier dataset is a candidate source; file-level licence, redistribution, SaaS and underlying input-data terms must be verified before any use. [S9]

## 10. Additional UK sources: necessary or not?

| Family | UK launch conclusion | Priority |
|---|---|---|
| Fuels/energy | **DEFRA sufficient** for common UK activity-based factors; use correct year and NCV/GCV basis. | P0 verify |
| Electricity | **DEFRA sufficient** for UK location-based activity factors; separate market-based evidence. | P0 verify |
| Transport/fleet/freight | **DEFRA sufficient** for common UK modes, fleet/freight, EV and WTT data. | P0 verify |
| Waste | **DEFRA sufficient** for common Scope 3 waste-disposal reporting; not for comparing waste options or all specialist pathways. Six narrow 2026 additions should be included when using 2026. | P0/P1 |
| Refrigerants/process gases | **DEFRA sufficient** where the published substance/process row matches; specialist industrial gases may need custom/specialist data. | P0 verify/P3 specialist |
| Water | **DEFRA sufficient** for mains supply and treatment; 2026 methodology refresh should be verified. | P0 verify |
| Materials | **DEFRA sufficient** for published material-use rows; product-specific LCA/EPD data later. | P0/P2 |
| Agriculture/land | Not a complete general factor family for every agricultural activity. | P3 |
| Industrial processes | Not universal; process-specific evidence may be required. | P3 |
| Spend | Separate Defra multiplier family, not company-reporting factors. | P3 |
| Waste-option analysis | WRAP CarbonWARM is not a replacement for DEFRA reporting factors; 2026 methodology says its outputs cannot be used for Scope 3 GHG reporting. | P3 |

## 11. UK organisations with overseas operations

### Required for UK launch

For UK activity: use GB/UK DEFRA rows. For an Irish site: existing IE/SEAI capability is available. A UK organisation’s headquarters country must not override the activity country. [C1][C2]

### Recommended multinational extension

| Activity/site | Factor treatment |
|---|---|
| UK site electricity/fuel/transport/waste | Existing GB DEFRA, selected by activity country/year/scope/unit. |
| Ireland site | Existing IE SEAI, with its CO2-only semantics and year/source disclosure. |
| Germany/France site electricity | Country-specific location-based factors required for accurate multinational reporting; EEA/national sources are later controlled candidates. |
| Germany/France fuels/transport/waste | Use an approved country/EU method only where boundary, unit, year and licence are verified; do not reuse UK factors merely because the organisation is UK-incorporated. |
| Overseas travel/hotel | DEFRA includes hotel/business-travel categories and some international activity logic, but country/mode/haul and underlying source terms must be checked. |
| Overseas electricity WTT/T&D | Full-set/IEA/national source path, not current UK flat import; later P2. |

**Germany/France factors are not required for a UK-only launch.** They are a controlled P2 multinational extension unless the launch contract explicitly promises consolidated overseas reporting.

## 12. Customer Custom Factors

Customer Custom Factors are suitable for:

- supplier-specific or measured electricity/fuel factors;
- product/process or facility-specific factors;
- specialist industrial gases/processes not represented by a suitable DEFRA row;
- customer-approved primary or supplier data with evidence;
- company-specific methods where the customer owns the source and accepts responsibility.

They must not be used to avoid a widely used authoritative DEFRA family such as ordinary UK electricity, fuels, water, common vehicles or standard business travel. Current D-cf-5 resolves an approved exact active customer factor before managed factors. If both are merely plausible, the product should require review/selection rather than silently choose; any change is **PRODUCT DECISION REQUIRED**. [C1][C2]

## 13. Licensing and commercial use

| Candidate | Assessment |
|---|---|
| DEFRA/DESNZ 2026 full/flat/methodology | 2026 methodology states Crown copyright and OGL v3. OGL permits commercial exploitation, adaptation, distribution and inclusion in products with attribution, subject to exclusions and third-party rights. Suitable in principle; retain attribution and verify each file notice. [S1][S2][S7] |
| DEFRA hotel factors | Current factor rows exist, but 2026 methodology identifies an external hotel-footprinting source/method. Underlying third-party rights and redistribution/SaaS terms are **LICENSING NOT VERIFIED**; do not assume that OGL for the government compilation licenses all underlying material. [S2] |
| DEFRA spend multipliers | Official UK government publication candidate. Commercial/SaaS/redistribution and any underlying input-data rights require file-specific verification. **LICENSING NOT VERIFIED at dataset-component level.** [S9] |
| SEAI | Existing capability; current live publication/workbook licensing was not retrievable here. **LICENSING NOT VERIFIED.** [S10] |
| IEA overseas factors | 2026 methodology points to IEA data; this research did not verify commercial access, redistribution or SaaS terms. **LICENSING NOT VERIFIED.** [S2][S14] |
| WRAP CarbonWARM | Methodological/reporting suitability is limited as above; licence/reuse was not assessed for a CarbonTally integration. **LICENSING NOT VERIFIED.** [S13] |
| Customer Custom Factors | Customer supplies/controls the source; require customer attestation, source reference and evidence under existing customer-factor workflow. This is not a licence grant to CarbonTally’s global catalogue. [C1][C2] |

## 14. Versioning and provenance recommendation

Use the existing model: `factor_source=DEFRA-DESNZ`, `factor_set=DEFRA-2025` or `DEFRA-2026`, `reporting_year`, `country=GB`, exact `unit`, row-specific `scope`, `provider_key=defra`, and `import_batch_id`. Create a distinct release for each source file and retain source filename, publication URL, SHA-256, provider version, row/factor ID, full-set/flat-file designation, methodology/changes report and attribution in provider artifacts/metadata. [C1][C2][S1][S4]

Maintain multiple reporting years. Never relabel a 2025 snapshot as 2026; historical snapshots must remain reproducible. Keep `factor_set`/batch history even when one active batch is selected for matching. The current natural-key/upsert limitation means parallel same-key methods need Product Owner approval before implementation. [C1][C2][S6]

## 15. Five highest-priority actions before UK launch

1. **P0 — Decide launch reporting years.** If 2026 activity is in scope, make the official 2026 DEFRA release the current-year verification/import gate; if only 2025, document that scope.
2. **P0 — Verify the 2026 flat mapping.** Confirm the six 2026-only IDs, the revised blank/zero corrections, source checksum, row counts, scopes, units, and that no 2025 rows are lost.
3. **P0 — Preserve existing coverage/provenance.** Keep DEFRA/SEAI/customer capabilities, factor source/set/year/country/unit/scope, batch checksum and immutable snapshots; do not rebuild providers.
4. **P0 — Validate common UK launch workflows.** Test offices, utility bills, fuel, fleet/EV, freight, business travel, water, waste, refrigerants, hotel and SECR evidence through existing mapping/matching/review paths.
5. **P1 — Make policy decisions visible.** Require activity country, distinguish location-based from market-based electricity, disclose CO2-only SEAI where relevant, and route ambiguous custom-versus-managed matches to review.

## 16. Explicitly not before UK launch

- No second general UK provider for ordinary fuels, electricity, transport, water or waste.
- No spend-based factor engine or mixed physical/spend factor set.
- No Germany/France/EU factor import unless overseas consolidated reporting is a launch commitment.
- No US/EPA/eGRID expansion.
- No WRAP/CarbonWARM waste-option integration as a Scope 3 reporting factor source.
- No separate LCA/EPD/product-factor platform.
- No change to schema, migrations, RLS, calculation, snapshot or customer-factor architecture without an approved decision.
- No silent replacement of customer factors or source precedence.

## 17. First factor expansion after UK launch

The first expansion should be a **controlled DEFRA 2026 release refresh/verification** if not completed for launch; this is a version update, not a new provider. After that, the first genuinely new factor expansion should be **country-aware location-based electricity for Germany and France**, using EEA/national sources after boundary, year, licensing and provenance verification. [S1][S5][S6]

## 18. Source register

| ID | Organisation/title/use | URL | Verification |
|---|---|---|---|
| C1 | CarbonTally canonical origin/main at d4dcca1eb11f86bcae497815c8592d688a7e305f | https://github.com/shomonrobie/CarbonTally/tree/d4dcca1eb11f86bcae497815c8592d688a7e305f | accessed 2026-08-24 |
| C2 | CarbonTally runtime/provider inspection: emission_factors, import_batches, customer_factors, factor matching, calculation, API, snapshots, migrations, provider code/tests; accessed 2026-08-24 | Repository evidence | accessed 2026-08-24 |
| C3 | CarbonTally generated DEFRA import metadata: output/json/import_summary.json, imported_rows.json, workbook_analysis.json, mapping_report.json; accessed 2026-08-24 | Repository evidence | accessed 2026-08-24 |
| S1 | UK Government/DESNZ, Greenhouse gas reporting: conversion factors 2026; updated 31 July 2026; full/flat/methodology/major changes files | https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026 | accessed 2026-08-24 |
| S2 | UK Government/DESNZ, 2026 GHG conversion factors methodology report | https://assets.publishing.service.gov.uk/media/6a2940543b15d05a7ce3202e/2026-GHG-conversion-factors-methodology-report.pdf | accessed 2026-08-24 |
| S3 | UK Government/DESNZ, 2026 major changes report | https://assets.publishing.service.gov.uk/media/6a2940653b15d05a7ce3202f/2026-GHG-conversion-factors-major-changes-report.pdf | accessed 2026-08-24 |
| S4 | UK Government/DESNZ, 2026 revised flat-format workbook (automatic processing) | https://assets.publishing.service.gov.uk/media/6a6c9748862aaf18d9c62ac9/ghg-conversion-factors-2026-flat-format-revised.xlsx | accessed 2026-08-24 |
| S5 | UK Government/DESNZ, 2026 full-set workbook | https://assets.publishing.service.gov.uk/media/6a29392bade52dc0882218a8/ghg-conversion-factors-2026-full-set.xlsx | accessed 2026-08-24 |
| S6 | UK Government collection, company-reporting factors; annual updates; activity-based versus spend multipliers | https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting | accessed 2026-08-24 |
| S7 | UK National Archives, Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ | accessed 2026-08-24 |
| S8 | UK Government, Environmental reporting guidelines including SECR requirements; updated 31 January 2019 | https://www.gov.uk/government/publications/environmental-reporting-guidelines-including-mandatory-greenhouse-gas-emissions-reporting-guidance | accessed 2026-08-24 |
| S9 | UK Government, UK and England carbon footprint to 2023; spend-based emissions multipliers 1997 to 2023 | https://www.gov.uk/government/statistics/uks-carbon-footprint | accessed 2026-08-24 |
| S10 | SEAI, Irish conversion factors publication area; live retrieval returned 403 in this environment | https://www.seai.ie/data-and-insights/seai-statistics/conversion-factors | accessed 2026-08-24 |
| S11 | GHG Protocol, Scope 2 Guidance | https://ghgprotocol.org/scope-2-guidance | accessed 2026-08-24 |
| S12 | GHG Protocol, Scope 3 Calculation Guidance | https://ghgprotocol.org/scope-3-calculation-guidance-2 | accessed 2026-08-24 |
| S13 | WRAP, Carbon Waste and Resources Metric, linked by 2026 methodology as an option-analysis tool; methodology says outputs cannot be used for Scope 3 GHG reporting | https://wrap.org.uk/resources/report/carbon-waste-and-resources-metric | accessed 2026-08-24 |
| S14 | IEA, overseas electricity/WTT sources referenced by 2026 methodology; commercial access terms not assessed | https://www.iea.org/data-and-statistics/data-product/emissions-factors-2024 | accessed 2026-08-24 |

Retrieval or licensing limitations are intentional. “LICENSING NOT VERIFIED” is not permission.
