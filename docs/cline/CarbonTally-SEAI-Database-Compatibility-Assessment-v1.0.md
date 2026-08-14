# CarbonTally — SEAI Ireland Factor Dataset & Database Compatibility Assessment v1.0

**Status:** READ-ONLY forensic analysis · no import performed · no code/schema/migration/test changed
**Date:** 2026-08-08
**Source analysed:** `SEAI-conversion-and-emission-factors.xlsx` (workbook) vs the current CarbonTally PostgreSQL schema, migrations, DEFRA provider implementation, factor domain model, matching engine and calculation engine.

---

## Executive Summary

The SEAI workbook is a compact, well-structured **Irish (Republic of Ireland) energy conversion and emission factor publication** for reporting year **2025** (workbook revision **V1.7**, dated 2026-06-19, "2025 values added"). It contains **28 published factor rows** (fuels + electricity variants), of which **20 rows carry a numeric emission-factor value**; the remaining 8 are biofuel/biomass rows that intentionally publish no CO2 factor (biogenic carbon = net zero).

The assessment concludes that **the existing CarbonTally canonical factor architecture can represent the SEAI dataset correctly without any database/schema change**:

* Every SEAI concept maps to an existing column or table: `provider_key` (via `import_batches`), `factor_source`, `factor_set`, `country`, `reporting_year`, `activity_type`, `unit`, `scope`, `co2e_multiplier`.
* The `emission_factors.country` CHECK constraint **already allows `'IE'`** (`country IN ('GB','IE')`) — the schema was explicitly designed for a second jurisdiction.
* SEAI emission factors are **CO2-only** (CH4/N2O excluded by source design). They are stored in the existing numeric `co2e_multiplier` column as the standard `quantity × multiplier` value; the CO2-vs-CO2e distinction is a documentation/metadata decision (factor source/set naming + batch provenance), not a schema blocker.
* The workbook's **conversion factors** (energy content MJ/kg, density kg/m³, specific volume, toe/t, primary-energy factors) are derivation inputs consumed **at import time**; the importer pre-computes per-physical-unit emission factors exactly as the workbook itself publishes them (`kgCO2/l`, `kgCO2/kg`, `kgCO2/m³`, `gCO2/kWh`). They must **not** become `emission_factors` rows, and **no separate table is required**.
* The multi-provider principle **DEFRA/UK/2025/Diesel ≠ SEAI/IE/2025/Diesel** is already guaranteed because `country` is part of the DB natural-key unique index and of the matching dimensions. A future same-country second provider (e.g. EPA alongside SEAI in IE) would require either distinct `activity_type` labels or (later, if ever needed) adding `provider` to the unique index — this is a forward caveat, not a blocker for SEAI today.
* **No matching-engine changes and no calculation-engine changes are required.**

**Final recommendation:** `RECOMMENDATION: EXISTING SCHEMA IS SUFFICIENT — PROCEED TO SEAI PROVIDER IMPLEMENTATION` (with the provider-logic design constraints in §14/§17).

---

## 1. Workbook Overview

| Property | Value |
|---|---|
| File name | `SEAI-conversion-and-emission-factors.xlsx` |
| Copies (identical; SHA-256 `e64f4f91cf5546767d80fc2fe6be252946bcafedbd957d6b2981c9cf3f640e6d`) | 1. `tools/carbon_data_factory/docs/SEAI-conversion-and-emission-factors.xlsx`<br>2. `tools/carbon_data_factory/factors/SEAI-conversion-and-emission-factors.xlsx`<br>3. `docs/cline/SEAI-conversion-and-emission-factors.xlsx` |
| Size | 110,711 bytes each |
| File type | `.xlsx` (OOXML). **No `.xls` legacy version exists** anywhere in the repository. |
| Producer | SEAI Energy Statistics Team (`epssu@seai.ie`) |
| Title | "Energy conversion and emission factors" — current table year **2025** |
| Status | "Ongoing" |
| Latest revision | V1.7 (2026-06-19): "2025 values added; Updates to Electricity Consumption and Gross Electricity Supply CO2 timeseries" |
| Version history | V1.0 (2022 data) → V1.1 → V1.2 → V1.3 (2023) → V1.4 → V1.5 (2024) → V1.6 → V1.7 (2025) |
| Calorific basis | **Net calorific value (NCV)** "unless otherwise stated" |
| Intended source | The **2025 table** on the sheet `Conversion and emission factors` (the workbook's timeseries sheets also provide 2001–2024 history) |
| Existing implementation status | `tools/carbon_data_factory/importers/providers/seai/` and `tools/carbon_data_factory/src/providers/seai/` contain **empty scaffolding only** (docstring stubs; empty `mapping.json`, empty `docs/providers/seai.md`, 0-byte `.ts` files) — **no validated SEAI importer exists yet**. |

---

## 2. SEAI Workbook Structure

The workbook contains **9 worksheets** (no hidden rows/columns; formula-driven with cached values present):

| Sheet | Dims | Role |
|---|---|---|
| `QAQC` | B2:E23 | Version history + author/contact (evidence for year/version) |
| `Conversion and emission factors` | B2:N69 | **Main "current year (2025)" table** — the intended import source |
| `Energy content timeseries` | B2:AC53 | MJ/kg (liquid/solid), MJ/m³ (gas), GCV & NCV, 2001–2025 |
| `Emission factors timeseries` | B2:AC67 | gCO2/kWh per fuel per year, 2001–2025 |
| `Density timeseries` | B2:AC48 | kg/m³ per fuel per year, 2001–2025 |
| `Primary energy timeseries` | B2:AC58 | Default PE factor 1.1 (fuels) + annual electricity PE factors |
| `road_petrol_blend` | A1:D26 | Year, Blend_kg_l, Blend_mj_kg, Blend_gCO2_kWh (2001–2025) |
| `road_diesel_blend` | A1:D26 | Year, Blend_kg_l, Blend_mj_kg, Blend_gCO2_kWh (2001–2025) |
| `GHG_elec` | A1:C26 | Year, Electricity_AFC_gCO2_kWh, Gross_Electricity_Supply_gCO2_kWh |

**Main sheet layout (`Conversion and emission factors`; 19 merged ranges for section headers; no hidden rows/cols):**

Header structure (rows 19–20), split per section: `B` category/section · `C` toe/t · `D` MJ/kg · `E` MJ/l · `F` gCO2/kWh · `G` gCO2/MJ · `H` kgCO2/kg · `I` kgCO2/l · `J` kg/m³ · `K` l/t · `L` PE factor · `M` Note · `N` Year.

Sections and rows (2025):

| Section | Rows | Row names |
|---|---|---|
| Liquid — Petroleum | 22–28 | Crude oil; Gasoline / petrol (100% petroleum); Kerosene; Jet Kerosene; Diesel / gasoil (100% petroleum); Residual fuel oil / fuel oil; LPG |
| Liquid — Biofuel / bioliquid | 31–36 | Bioethanol; Biodiesel ME; Biodiesel HVO; Biodiesel CHVO; Biopropane; Biojet HVO |
| Liquid — Blended | 39–40 | Road diesel (avg. biofuel content); Road petrol (avg. biofuel content) |
| Solid — Fossil fuel | 45–51 | Petroleum coke; Bituminous coal; Anthracite; Lignite; Milled peat; Sod peat; Peat briquettes |
| Solid — Biomass | 54–55 | Wood pellets & briquettes; Wood logs & chips |
| Gas | 59–60 | Natural gas (GCV); Natural gas (NCV) |
| Electricity | 64–65 | Electricity consumption; Gross electricity supply |

Notes column content includes: LPG "70% propane & 30% butane"; biodiesel ME "5.4% fossil carbon per EPA NIS 2025"; road blends "Average diesel/petrol-biofuel blend in 2025"; petroleum coke / natural gas / electricity "Provisional values for 2025"; wood "Assumes 25% moisture content"; electricity scope methodology notes.

All main-sheet cells are **formulas** (`INDEX/MATCH` into the timeseries sheets + arithmetic: toe/t = MJ/kg×1000/41868; MJ/l = MJ/kg×density/1000; gCO2/MJ = gCO2/kWh/3.6; kgCO2/kg = gCO2/MJ×MJ/kg/1000; kgCO2/l = kgCO2/kg×density/1000; specific vol = 10⁶/density; gas NCV = GCV×0.902). **Cached values are present** (openpyxl `data_only=True` resolves every cell).


---

## 3. SEAI Data Dictionary

Conceptual dictionary for the SEAI dataset (fields observed on the main sheet + supporting timeseries).

| Field | Meaning | Example (2025) | Data Type | Required? | Factor Attribute? | Conversion Attribute? |
|---|---|---|---|---|---|---|
| Section / category | Fuel family group | `Liquid — Petroleum` | text | yes (source) | yes (→ label prefix) | no |
| Activity name | Fuel/energy description | `Diesel / gasoil (100% petroleum)` | text | yes | yes | no |
| Energy content — mass | NCV per kg | `43.308259` MJ/kg (diesel) | numeric | yes | no | **yes** |
| Energy content — volume | NCV per litre | `36.595479` MJ/l (diesel) | numeric | liquids only | no | **yes** |
| Energy content — gas volume | NCV per m³ | `35.478706` MJ/m³ (gas NCV) | numeric | gas only | no | **yes** |
| Energy content — toe | tonne-of-oil-equivalent | `1.0344` toe/t (diesel) | numeric | liquids/solids | no | **yes** |
| Emission factor — energy | gCO2/kWh (NCV) | `263.868` (diesel) | numeric | yes | **yes** (canonical) | no |
| Emission factor — energy | gCO2/MJ (NCV) | `73.296667` (diesel) | numeric | derived | yes | no |
| Emission factor — mass | kgCO2/kg fuel | `3.174351` (diesel) | numeric | derived | yes | no |
| Emission factor — volume | kgCO2/l fuel | `2.682327` (diesel) | numeric | liquids | yes | no |
| Emission factor — gas volume | kgCO2/m³ | `2.005357` (gas NCV) | numeric | gas | yes | no |
| Density | kg/m³ | `845` (diesel) | numeric | liquids | no | **yes** |
| Specific volume | l/t | `1183.43` (diesel) | numeric | liquids | no | **yes** |
| PE factor | primary-energy factor | `1.1` (fuels); `1.739168` (elec consumption) | numeric | yes | no | **yes** |
| Scope | GHG Protocol scope | `Scope 1` (fuels); `Scope 2 + 3` (elec consumption) | text | derived | yes | no |
| Country | jurisdiction | `IE` | text | dataset-level | yes | no |
| Reporting year | year the factor applies to | `2025` | int | yes | yes | no |
| Source | provider authority | `SEAI` | text | yes | yes | no |
| Factor set / version | named vintage | `SEAI-2025` | text | yes | yes | no |
| Methodology basis | NCV / GCV | `NCV` (gas NCV vs GCV variants) | text | yes | metadata | no |
| Gas coverage | species included | `CO2 only` (CH4/N2O excluded) | text | yes | metadata | no |
| Notes | footnotes/provisional flags | `Provisional values for 2025` | text | no | metadata | no |

**Emission factors vs conversion factors vs metadata vs reference values** — classification:
* **Emission factors**: the `gCO2/kWh` (timeseries) and the derived `gCO2/MJ`, `kgCO2/kg`, `kgCO2/l`, `kgCO2/m³` columns on the main sheet.
* **Conversion factors**: energy content (`MJ/kg`, `MJ/l`, `MJ/m³`, `toe/t`), `density` (`kg/m³`), `specific volume` (`l/t`), `PE factor`.
* **Metadata**: QAQC revision log, notes column, "Provisional 2025" flags, NCV basis, "CO2 only" scope statements, biomass/biogenic assumptions, author/contact.
* **Lookup/reference values**: year headers (2001–2025) in the timeseries sheets; blend composition columns in `road_petrol_blend`/`road_diesel_blend`; electricity time series in `GHG_elec`.
* **Notes/instructions**: the comments blocks at the top of each sheet (methodology statements).


---

## 4. SEAI Factor Semantics

**Emission factors are CO2-only** (direct combustion CO2). Source comments state explicitly: "Emission factors for CH4 and N2O are not included in this spreadsheet"; "with the exception of electricity, the emission factors include only direct CO2 emissions from combustion of fuels". SEAI refers users to the EPA National Inventory Submissions for CH4/N2O. This is a deliberate **CO2 (not CO2e)** factor family.

**Combustion fuels — the emission factor is per unit of ENERGY, and per-physical-unit factors are derived:**

```
WHAT × CONVERSION → EMISSIONS
Fuel quantity (kg)   × kgCO2/kg   = kg CO2     (mass basis)
Fuel quantity (l)    × kgCO2/l    = kg CO2     (volume basis)
Fuel quantity (m³)   × kgCO2/m³   = kg CO2     (gas volume basis)
Fuel energy (kWh)    × kgCO2/kWh  = kg CO2     (energy basis, NCV)

kgCO2/kg   = (gCO2/kWh ÷ 3.6) × MJ/kg ÷ 1000
kgCO2/l    = kgCO2/kg × density(kg/l) / 1000  (density from kg/m³)
kgCO2/m³   = (gCO2/kWh ÷ 3.6) × MJ/m³ ÷ 1000
gCO2/MJ    = gCO2/kWh ÷ 3.6
```

The workbook publishes **all four** derived per-physical-unit factors directly (its own formulas), so the importer can consume the published values rather than recomputing.

**Electricity — two distinct factor families (both gCO2/kWh, CO2 only):**
* **Electricity consumption** (2025: `197.803384` gCO2/kWh): CO2 arising within Ireland per unit of electricity available for final consumption — includes generation, transmission & distribution losses and power-plant own-use. Source scope note: includes **Scope 2** (generation) and **Scope 3** (T&D losses, own-use) per GHG Protocol. Imports not included.
* **Gross electricity supply** (2025: `178.327674` gCO2/kWh): CO2 per unit of gross supply = gross production (excl. pump/battery storage) + net imports — generation only.
* PE factors (primary energy): consumption `1.739168`, gross supply `1.576067` (2025).

**Biofuels & biomass** publish **no emission factor** (net biogenic CO2 = zero by assumption); they carry energy-content, density and PE factors only. Biodiesel ME carries a 5.4% fossil-carbon factor per EPA NIS 2025 (`4.06 gCO2/MJ`; `0.151 kgCO2/kg`).

**Methodologies used:** fuel/energy-based (fuels), activity-based for electricity (gCO2 per kWh). **No** spend-based or distance-based factors. Transport factors are fuel-based (road diesel/petrol blends); no per-km factors are published.


---

## 5. Conversion Factors vs Emission Factors

**Both exist in the workbook, and they play different semantic roles:**

* **Emission factors** answer "how much CO2 per unit of consumption/energy". They are the `gCO2/kWh` (canonical energy basis), and the derived `gCO2/MJ`, `kgCO2/kg`, `kgCO2/l`, `kgCO2/m³` columns.
* **Conversion factors** answer "how much energy/density per physical unit". They are energy content (`MJ/kg`, `MJ/l`, `MJ/m³`), density (`kg/m³`), specific volume (`l/t`), `toe/t`, and the primary-energy factor (`PE`).

**How they relate (the SEAI calculation methodology):** the emission factor per physical unit IS the emission factor per energy unit scaled by the conversion factors (see §4). The workbook itself performs this derivation with formulas. The conversion factors are therefore **not independently reportable emissions quantities** — they are inputs that produce the final per-unit emission factors.

**Decision — both should NOT become rows in `emission_factors`:** only the final **emission factors** (per physical unit) become rows. The conversion factors:
1. are used by the importer to validate/derive the published per-unit factors (or are read directly from the published derived columns), and
2. are captured for provenance in `import_batches` (source file + checksum + version) and, if desired, in per-import metadata — the domain already preserves source rows in `EmissionFactor.metadata` (the DEFRA importer does exactly this).

**A separate conversion-factor table is NOT necessary.** Rationale: the runtime path (`quantity × co2e_multiplier`) consumes precomputed per-unit factors; nothing in the matching or calculation engine needs live conversion chains, because every published physical-unit factor is final. This matches how DEFRA factors are stored (DEFRA publishes factors already expressed per physical unit — SEAI does too, in its derived columns).


---

## 6. SEAI Data Quality Findings

| Finding | Detail | Count / Evidence |
|---|---|---|
| Missing (intentional) factor values | Biofuel/biomass rows carry `-` for all emission-factor columns (biogenic net-zero). | **8 rows** (Bioethanol; Biodiesel HVO/CHVO; Biopropane; Biojet HVO; Wood pellets & briquettes; Wood logs & chips; + note that Biodiesel ME HAS a 5.4% fossil-carbon value) |
| Formula-driven values | Every main-sheet value is an `INDEX/MATCH` + arithmetic formula. **Cached values are present**, so `openpyxl(data_only=True)` resolves them. | 98 formula cells on `Energy content timeseries`; all main-sheet cells are formulas |
| Derived values | gas NCV = GCV × 0.902 (formula); gCO2/MJ = gCO2/kWh ÷ 3.6; kgCO2/l derived from density | verified by inspection |
| "Provisional" flags | `Provisional values for 2025` on Petroleum coke, Natural gas (GCV & NCV), Electricity, Milled peat | 4+ rows |
| Duplicate-risk representations | `road_petrol_blend`/`road_diesel_blend` duplicate the main-sheet blended rows; `GHG_elec` duplicates the electricity timeseries; `Emission factors timeseries` duplicates the main-sheet gCO2/kWh column | 3 sheets |
| Mixed units | gCO2/kWh, gCO2/MJ, kgCO2/kg, kgCO2/l, kgCO2/m³, MJ/kg, MJ/l, MJ/m³, kg/m³, l/t, toe/t, `-` (dimensionless PE) | 11 distinct unit strings |
| Text-as-value | `-` used for "no value" instead of blank cells | biofuel/biomass rows |
| Merged cells | Section headers merged across columns (19 ranges on main sheet) | e.g., `B19:B20`, `F19:I19` |
| No per-row scope | Scope is implicit by fuel family (fuels → Scope 1; electricity consumption → Scope 2 + 3) | derived at import |
| No per-row country | Dataset is Ireland-specific; country not present in any cell | assign `IE` for every row |
| No CH4/N2O | Not published (by design); CO2-only | source comment |
| Blank rows / totals | No subtotal/total rows; section headers are textual rows to skip | — |
| Year/version metadata | QAQC V1.7 (2026-06-19); main sheet year `2025`; timeseries 2001–2025 | explicit |

**Row-count summary (2025 main sheet):** 28 published rows; 20 with numeric emission factors; 8 without (biofuel/biomass, biogenic zero); electricity contributes 2 factor families (consumption / gross supply).


---

## 7. Current CarbonTally Database Schema

Source of truth: the applied migrations (`supabase/migrations/*.sql`) **verified live** against the authoritative database (read-only introspection, `postgres@54326/postgres`).

### `public.emission_factors`

| Column | Type | Nullable | Default / Notes |
|---|---|---|---|
| id | uuid | NO | PK, `DEFAULT extensions.uuid_generate_v4()` |
| reporting_year | integer | NO | — |
| activity_type | character varying | NO | RC2 activity label |
| co2e_multiplier | numeric | NO | `CHECK (co2e_multiplier >= 0)` |
| created_at | timestamptz | YES | `DEFAULT now()` |
| updated_at | timestamptz | YES | `DEFAULT now()` |
| unit | text | YES | free text |
| scope | text | YES | free text |
| factor_source | text | YES | e.g. `DEFRA-DESNZ`, `SEAI` |
| factor_set | text | YES | e.g. `DEFRA-2025`, `SEAI-2025` |
| country | character varying | YES | `CHECK (country IN ('GB','IE'))` — **`IE` already allowed** |
| region_deprecated | character varying | YES | legacy |
| import_batch_id | uuid | YES | `FK → import_batches(id) ON DELETE SET NULL` |

**Unique constraint (natural key):** `emission_factors_year_activity_country_uniq` on `(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))`.

**Indexes:** PK (id); the natural-key unique index; `idx_emission_factors_import_batch`.

**Natural-key assumption (existing):** a factor is identified by `(year, activity_type, country, unit, scope)` — **provider/source/factor_set are NOT part of the key.**

### Other relevant tables

* `public.import_batches` — versioned import provenance: `provider_key`, `provider_version`, `source_file`, `source_checksum`, `reporting_year`, `status` (`pending|importing|completed|failed|rolled_back`), `rows_total/imported/skipped/duplicate`, `errors`, `is_active`, `created_by`, `rolled_back_from`. **Capable of recording the SEAI source/version/checksum.**
* `public.factor_aliases` — org-scoped or global alias: `alias_text`, `target_activity_type`, `target_provider_key` (provider-aware aliases), unique per (org-or-global, alias_text).
* `public.calculation_snapshots`, `public.emissions_logs`, `public.domain_events`, `public.audit_trail` — calculation/log/event/audit persistence (unchanged by this assessment).


---

## 8. Current DEFRA Provider Architecture

Pipeline (actual code, `src/providers/defra/*` + `src/commands/import_defra.py`):

```text
DEFRA source workbook
   → parser (openpyxl: classify sheets data/documentation/unsupported, parse rows, SHA-256)
   → mapper (normalise text/decimals; build activity labels; natural key; preserve source row in metadata)
   → validator (DB rules: no-factor-value skip, duplicates, warnings)
   → exporter (deterministic idempotent SQL `INSERT ... WHERE NOT EXISTS`, full JSON export, summary/statistics)
   → loader (psycopg2 upsert by natural key; mode `sync`/`replace`; counts inserted/updated)
```

Key properties:
* **7,029 DEFRA-2025 factors persisted** (GB, 2025, `factor_source='DEFRA-DESNZ'`, `factor_set='DEFRA-2025'`).
* The importer CLI is `python -m src.commands.import_defra` (`--no-db`, `--mode`, `--db-url`).
* Source-row fidelity: fields with no `emission_factors` column are preserved in `EmissionFactor.metadata` (JSON) — **the architecture already supports per-factor metadata without schema change**.
* Idempotency by natural key (upsert); `import_batches` integration added via migration M1/M2 (import_batch_id column, nullable).


---

## 9. Current Factor Domain Model

`backend/domain/factor.py` — `EmissionFactor` (frozen dataclass):

| Field | First-class DB column? |
|---|---|
| id | yes |
| reporting_year | yes |
| activity_type | yes |
| co2e_multiplier | yes |
| unit | yes |
| scope | yes |
| factor_source | yes |
| factor_set | yes |
| country | yes (default `GB`) |
| provider_key | yes (derived via `import_batches` join) |
| import_batch_id | yes |
| natural_key | derived `(year, activity, country, unit, scope)` |

**Concepts NOT first-class (metadata only):** methodology (NCV/GCV), factor type (CO2 vs CO2e), gas species, category hierarchy (encoded in the label text), conversion factors, confidence, per-factor provenance detail (kept at batch level in `import_batches`), notes.

The `FactorSet`/`FactorSetMetadata` domain types (provider_key, year, version, row_count, checksum, source_path) mirror the `import_batches` provenance concept.

---

## 10. Current Matching Engine Architecture

`backend/engines/factor_matching.py` + `matching_stages.py` + `infra/search_index.py`:

* **Stages (in order):** `exact_match` → `natural_key` → `alias_match` → `keyword_search` → `fuzzy_match` → `semantic_match` (inert until enabled).
* **MatchRequest dimensions:** `activity`, `country`, `reporting_year`, `unit`, `scope`, `preferred_provider`, `max_stages`.
* **Search index filters:** `keyword_search(query, unit, country, provider, limit)`; natural-key map keyed by `(reporting_year, activity_type, country, unit, scope)`.
* **Config:** `restrict_country`, `prefer_provider`, thresholds, max_suggestions.
* **Ambiguity handling:** multiple candidates produce `no_match` + `suggestions` for manual selection; `MatchResult.status` ∈ {matched, no_match, ambiguous}.
* **Key assumption check:** the engine does **not** assume `activity + unit = unique factor`. The natural-key stage uses `(year, activity, country, unit, scope)`, and every retrieval stage filters by `country` and `provider` from the request. Ambiguity is an explicit, handled outcome.


---

## 11. DEFRA vs SEAI Comparison

| Dimension | DEFRA (UK) | SEAI (Ireland) | Existing DB supports both? | Action |
|---|---|---|---|---|
| Provider | `defra` | `seai` | Yes — `provider_key` via `import_batches` | set `provider_key='seai'` |
| Source | `DEFRA-DESNZ` | `SEAI` | Yes — `factor_source` | set `factor_source='SEAI'` |
| Country | `GB` | `IE` | Yes — column + CHECK allows `IE` | set `country='IE'` |
| Reporting year | `2025` | `2025` | Yes — column | set 2025 |
| Factor set | `DEFRA-2025` | `SEAI-2025` | Yes — `factor_set` | set `factor_set='SEAI-2025'` |
| Activity | taxonomy `Fuels > Liquid fuels > Diesel ... [litres]` | `Diesel / gasoil (100% petroleum)` | Yes — `activity_type` text | construct canonical labels (importer logic) |
| Category | in label hierarchy | sections (Liquid/Solid/Gas/Electricity) | Yes — label text | prefix labels (e.g. `Fuels > Liquid fuels > ...`) |
| Unit | litres, kWh, kg, tonnes, km, m³ | kgCO2/l, kgCO2/kg, kgCO2/m³, gCO2/kWh | Yes — `unit` text | canonical unit strings + per-unit factor |
| Scope | Scope 1/2/3 labels | fuels=Scope 1; electricity=Scope 2+3 | Yes — `scope` text | assign per family |
| Factor value | kg CO2e per unit | kg CO2 per unit (CO2-only) | Yes — `co2e_multiplier` numeric | store value; document CO2-only semantics |
| Factor type | CO2e (CH4+N2O included) | CO2 only | Partial — no column | metadata/factor_set naming (B) |
| Methodology | activity-based per unit | NCV energy-based + derived units | Partial — no column | metadata (NCV) + label/notes (B) |
| Conversion factors | none published separately | energy content/density/PE published | Not applicable as rows | consume at import; do not store as rows |
| Notes | workbook notes | per-row notes + QAQC | Yes — metadata pattern | metadata |
| Provenance | workbook checksum in import_batches | QAQC version + file checksum | Yes — `import_batches` | record V1.7 + SHA-256 |
| Gas coverage | CO2e aggregates | CO2 only (CH4/N2O excluded) | Partial — no column | metadata (B/E) |

---

## 12. Multi-Provider Architecture Assessment

**Principle under test:** `DEFRA / UK / year / factor set / activity / unit` must be distinguishable from `SEAI / Ireland / year / factor set / activity / unit`, even with identical or similar activity+unit.

**Result: PASS for DEFRA-GB vs SEAI-IE, without schema change.**

1. **Database:** the natural-key unique index is `(reporting_year, activity_type, country, unit, scope)`. `DEFRA-2025/GB/.../Diesel/litres` and `SEAI-2025/IE/.../Diesel/litres` differ by `country` → **two distinct rows**, no conflict.
2. **Domain:** `EmissionFactor.natural_key` includes `country`; `provider_key` is carried on every factor (derived from the owning batch).
3. **Matching:** `MatchRequest` carries `country` and `preferred_provider`; `keyword_search` and the natural-key map filter on both. A UK user matching "Diesel" resolves to the GB/DEFRA factor; an Irish user (country=IE) resolves to the IE/SEAI factor.

**Forward caveat (documented, not a blocker):** the natural key does **not** include `provider`/`factor_source`/`factor_set`. If a second Irish provider (e.g. EPA) ever publishes the **same `activity_type`, `unit`, `scope`, `country=IE`, `year`** as SEAI, the two rows would collide at the unique index. Mitigations available without schema change: (a) activity-label discipline (distinct `activity_type` per provider), or (b) later, if unavoidable, extend the unique index to include `factor_source`/`provider` (a deliberate, separate schema decision — not required for SEAI).

**Architectural principle confirmed:** provider/source/country are part of factor identity and matching context (the correction documented in `docs/cline/CarbonTally — Ireland Provider Expansion & Cross-Provider Validation v1.0.md`), not a separate mapping engine. The existing canonical architecture supports this.


---

## 13. Database Compatibility Matrix

| SEAI Requirement | Classification | Evidence / Notes |
|---|---|---|
| Provider (`seai`) | **A — Fully supported** | `provider_key` derived from `import_batches`; `factor_source` column |
| Source (`SEAI`) | **A** | `factor_source` text column |
| Country (`IE`) | **A** | column + CHECK allows `'IE'` (verified live) |
| Reporting year (2025) | **A** | `reporting_year` integer |
| Factor set (`SEAI-2025`) | **A** | `factor_set` text column |
| Activity (fuel labels) | **B — Metadata/label design** | `activity_type` text; canonical label taxonomy must be defined (importer logic) |
| Category (Liquid/Solid/Gas/Electricity) | **B** | encode in `activity_type` label hierarchy |
| Unit (litres, kg, m³, kWh) | **C — Provider logic** | canonical unit strings; must satisfy calculation-engine unit equality |
| Scope (Scope 1; Scope 2+3 electricity) | **A** | `scope` text column |
| Factor value (kg CO2/unit) | **A** | `co2e_multiplier` numeric (`>= 0` CHECK satisfied) |
| Factor type (CO2 vs CO2e) | **B** | no column; factor_set/source naming + metadata; column named `co2e` is a documented semantic caveat |
| Methodology (NCV) | **B** | metadata / label + batch provenance |
| Conversion factors (energy content, density, PE) | **C** | consumed at import time to produce per-unit factors; not stored as rows |
| Notes / provisional flags | **B** | per-factor metadata pattern (DEFRA precedent) |
| Provenance (version V1.7, checksum) | **A** | `import_batches` columns |
| Gas coverage (CO2-only) | **B/E** | not expressible as a column; record in metadata and batch notes; confirm product reporting requirements |
| Historical years (2001–2024) | **A** | `reporting_year` per row; import as separate vintages if required |

Legend: **A** fully supported · **B** supported via metadata/label design · **C** provider/app logic only · **D** schema change required · **E** unclear (requires clarification).

**No requirement is classified D.**


---

## 14. Schema Change Assessment

### OPTION 1 — NO SCHEMA CHANGE (RECOMMENDED)

**Why the current schema can represent SEAI correctly:**
* Every SEAI field maps to an existing column/table (see §13). The `country` CHECK already includes `'IE'`; `factor_source`/`factor_set`/`scope`/`unit` are free-text; `co2e_multiplier` is a plain numeric multiplier; `import_batches` provides full provenance (provider, version, source file, checksum, counts).
* The workbook's conversion factors are derivation inputs — precomputed into per-physical-unit emission factors at import time, exactly as SEAI publishes them.
* Multi-provider distinction works via `country` in the natural key (§12).

**Provider-logic constraints required at implementation (no schema impact):**
1. Set `country='IE'`, `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `provider_key='seai'` for every row; create a batch in `import_batches` with `provider_key='seai'`, `provider_version='2025 (V1.7)'`, source checksum.
2. Import one **canonical emission factor per physical unit** per fuel family from the published derived values: liquid fuels → `kgCO2/l` (e.g. diesel `2.682327`), solid fuels → `kgCO2/kg`, gas → `kgCO2/m³` (NCV), electricity → `kgCO2/kWh` (`0.197803` consumption / `0.178328` gross supply). Do **not** import the energy/density/PE conversion columns as rows.
3. Define canonical `activity_type` labels, e.g. `Fuels > Liquid fuels > Diesel / gasoil (100% petroleum) (kg CO2) [litres]` — reusing the DEFRA label grammar while keeping SEAI source names.
4. Assign `scope`: fuels → `Scope 1`; electricity consumption → `Scope 2` (note: SEAI includes T&D losses/own-use = Scope 3 in the consumption factor — record in metadata/notes); gross supply → `Scope 2` (generation).
5. Skip the 8 biofuel/biomass rows with `-` emission values (report as `skipped_no_factor`), or import with `co2e_multiplier=0` + explicit metadata if product rules require zero-carbon fuels to appear.
6. Record the CO2-only semantics in batch provenance + per-factor metadata; do not silently label them "CO2e".
7. Import the 2025 table as the primary vintage; 2001–2024 history optional (each year is a separate natural-key row).

### OPTION 2 — SCHEMA CHANGE (NOT REQUIRED)

No table/column/constraint change is proposed. The only forward-looking item is the same-country multi-provider caveat (§12), which today is handled by label discipline and does not require a migration.


---

## 15. Matching Engine Impact

**No changes required for SEAI support.** Evidence:
* Matching already filters by `country`, `provider` (`preferred_provider`), `unit`, `scope`, `reporting_year` — every SEAI dimension is a matching dimension.
* Natural-key matching includes `country`; DEFRA-GB and SEAI-IE never collide.
* Ambiguity (e.g., both SEAI blended diesel and SEAI 100%-petroleum diesel matching "Diesel") is handled by the existing `suggestions`/`ambiguous` outcome.

**Recommended (provider-logic, not engine changes):** seed global `factor_aliases` mapping common Irish vocabulary (e.g. `diesel` → SEAI diesel label, `m3`/`m³` normalization) using `factor_aliases.target_provider_key='seai'`; keep unit strings canonical so the calculation-engine unit equality holds.

---

## 16. Calculation Engine Impact

**No calculation changes required.** Evidence:
* The engine computes `quantity × co2e_multiplier` with a unit-equality guard. SEAI factors precomputed per physical unit (`kgCO2/l`, `kgCO2/kg`, `kgCO2/m³`, `kgCO2/kWh`) fit this contract exactly.
* No conversion chains are needed at runtime (all derived factors are final).
* Scope labels pass through unchanged; snapshots/audit/events are provider-agnostic.


---

## 17. Future SEAI Import Architecture (conceptual — NOT implemented)

```text
SEAI workbook (tools/carbon_data_factory/docs/SEAI-conversion-and-emission-factors.xlsx)
   → SEAI reader (openpyxl, data_only=True for cached values; SHA-256 checksum)
   → SEAI parser (classify sheets: main data sheet 'Conversion and emission factors'; documentation;
                  ignore timeseries/blend/GHG_elec as reference data — single-source rule)
   → SEAI normalizer (parse numbers/'−'; NCV basis; resolve cached values; handle merged headers)
   → SEAI mapper (build canonical activity_type labels; pick canonical physical-unit emission factor;
                  assign scope; set country=IE, factor_source=SEAI, factor_set=SEAI-2025, year=2025;
                  preserve source row + notes + conversion factors in metadata)
   → SEAI validator (DB rules: skip no-value rows with reason; duplicate detection by natural key;
                     unit sanity checks; non-negative values)
   → canonical factor model (EmissionFactor / import batch)
   → load via existing exporter pattern (idempotent SQL/JSON + psycopg2 upsert by natural key)
   → import_batches row (provider_key='seai', provider_version='2025 (V1.7)',
                         source_file, source_checksum, rows_imported=20, skipped=8, duplicates=0)
```

**What becomes a factor:** the 20 rows with numeric emission factors (one canonical physical-unit factor per fuel family + electricity consumption/gross supply).

**What becomes metadata:** source row, notes ("Provisional 2025", blend assumptions, moisture content), NCV basis, CO2-only statement, conversion factors (energy content/density/PE), EPA reference for biodiesel ME.

**What becomes provider/source information:** `import_batches` (provider_key, version, checksum, counts) + `factor_source='SEAI'`, `factor_set='SEAI-2025'`.

**What becomes aliases:** Irish vocabulary (e.g. "petrol", "diesel", "natural gas", "electricity") → SEAI labels, with `target_provider_key='seai'`.

**What is ignored:** QAQC sheet, comments blocks, timeseries/blend/GHG_elec sheets (reference only), section-header rows, `-` placeholders.

**What requires manual review:** provisional 2025 values (petroleum coke, natural gas, electricity), biogenic-zero policy for biofuels/biomass, the CO2-vs-CO2e product-label decision, and whether electricity "consumption" (Scope 2+3) vs "gross supply" (Scope 2) should both be exposed.

---

## 18. Import Risks

**Overall risk: MEDIUM.**

| Risk | Rating | Rationale |
|---|---|---|
| Schema risk | LOW | No change needed; `IE` already allowed; all columns exist |
| Mapping risk | MEDIUM | Label taxonomy + canonical unit selection are new design decisions; CO2-only semantics must be labelled correctly |
| Data-quality risk | MEDIUM | Formula-driven with cached values (must read cached values); "Provisional 2025" flags; biogenic-zero rows |
| Unit risk | MEDIUM–HIGH | 11 distinct unit strings; per-unit factor derivation must pick the correct published values (kgCO2/l vs kgCO2/kg vs kWh) |
| Duplicate risk | MEDIUM | Blend sheets + GHG_elec duplicate main-sheet values; single-source import rule required |
| Calculation risk | LOW | Precomputed per-unit factors fit `quantity × multiplier` exactly |
| Matching risk | MEDIUM | SEAI labels differ from DEFRA taxonomy; aliases + country/provider filters mitigate; ambiguity already handled |
| Provenance risk | LOW | `import_batches` records version/checksum/counts; workbook QAQC gives explicit version V1.7 |


---

## 19. Recommended Implementation Plan (future sequence — NOT executed now)

1. Approve this assessment (schema decision: no change).
2. Approve the SEAI data model / label taxonomy / canonical units / CO2-only labelling.
3. Implement SEAI provider (reader → parser → normalizer → mapper → validator → exporter/loader), mirroring `src/providers/defra`.
4. Implement SEAI importer CLI (mirror `src/commands/import_defra.py`).
5. Add SEAI fixture tests (parser/mapper/validator on a snapshot of the workbook).
6. Import SEAI into the isolated test database (`carbontally_test`), never the authoritative DB during development.
7. Validate factor counts (expect 20 factor rows for 2025) and natural-key uniqueness (country=IE).
8. Validate matching: exact/natural-key/alias/keyword/fuzzy/ambiguous/no-match; UK vs Ireland provider isolation.
9. Validate calculations with SEAI factors (unit equality, snapshot, content hash, audit/events).
10. Run DEFRA regression suite (7,029 factors intact; all existing tests green).
11. After approval, import into the authoritative database (idempotent upsert by natural key).
12. Verify final counts (DEFRA 7,029 + SEAI 20 for 2025) and provenance (`import_batches`).

---

## 20. Final Recommendation

The existing CarbonTally architecture is already multi-provider/multi-country capable: provider/source/country/factor-set/year are first-class factor identity, matching is country/provider/year/unit/scope aware, the `country` CHECK pre-allows `'IE'`, and `import_batches` provides full provenance. The SEAI dataset's emission factors fit the canonical `quantity × co2e_multiplier` model with conversion factors resolved at import time, requiring only provider logic (label taxonomy, canonical units, CO2-only labelling) and **no database, matching-engine or calculation-engine change**.

The SEAI integration should be implemented as a new provider plugin in the existing `src/providers/` architecture — a provider expansion, not a schema or engine project. The only forward caveat is the same-country multi-provider natural-key collision risk (SEAI + EPA in IE), which is handled today by activity-label discipline and only warrants a future migration if a second Irish provider is actually added.

RECOMMENDATION: EXISTING SCHEMA IS SUFFICIENT — PROCEED TO SEAI PROVIDER IMPLEMENTATION

