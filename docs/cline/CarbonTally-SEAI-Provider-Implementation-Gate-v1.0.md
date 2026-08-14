# CarbonTally — SEAI Provider Implementation Gate v1.0

**Status:** READ-ONLY implementation-design verification · no code/schema/migration/test/data changes · no import
**Date:** 2026-08-08
**Base document:** `docs/cline/CarbonTally-SEAI-Database-Compatibility-Assessment-v1.0.md`
**Scope:** Four gate questions (metadata/provenance, CO2-vs-CO2e, electricity representation, exact 28-row mapping) plus canonical units, import-batch behaviour, natural-key risk.

---

## 1. Executive Conclusion

The existing CarbonTally architecture remains sufficient to represent the SEAI 2025 dataset **without any schema change**, but two claims from the prior assessment needed **correction against actual code**:

1. **Per-factor metadata is NOT persisted in the database.** The DEFRA provider model carries a `metadata` dict and the JSON export preserves it, but the DB loaders persist only the 8 `emission_factors` columns. There is **no database column** for per-factor metadata today. For SEAI v1 this is fully covered by `import_batches` provenance + existing columns (`factor_source`, `factor_set`, `scope`, label suffix) — **no metadata column is required**.
2. **All 7,029 DEFRA rows have `import_batch_id = NULL`.** The DEFRA CLI loader never creates `import_batches` rows nor links factors (the batch integration lives only in the data layer and migrations). The SEAI importer **should** create a batch and populate `import_batch_id` so `provider_key='seai'` is correctly derived by the factor repository.

**CO2-vs-CO2e:** SEAI factors are CO2-only; the DB column and snapshot column are named `co2e`. No customer-facing output exists yet (Phase 10 API/reporting not built), and `factor_source`/`factor_set` ARE carried on factors and snapshots — so the product **can** distinguish SEAI CO2 from DEFRA CO2e downstream. This is **not a blocker**, but the labelling decision must be agreed before any reporting phase renders it.

**Exact mapping:** 28 main-sheet rows → **20 imported factor records, 8 skipped** (7 rows have no published factor value — biogenic net-zero; 1 row is the Natural gas (GCV) variant whose physical-unit factor duplicates the NCV row).

**Verdict: GO WITH CONDITIONS — IMPLEMENT ONLY AFTER CONDITIONS ARE SATISFIED** (conditions are design approvals listed in §10 — none require schema or code changes to the existing engine layer).

---

## 2. Metadata / Provenance Finding

**A. Does the backend `EmissionFactor` domain model have a metadata field?** **No.** `backend/domain/factor.py` defines `EmissionFactor` with exactly: `id, reporting_year, activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country, provider_key, import_batch_id, natural_key`. There is no `metadata` field.

**B/C/D. Where does "metadata" actually live?** The prior assessment's claim "source-row fidelity is preserved in `EmissionFactor.metadata`" refers to the **provider-side model** in `src/providers/defra/models.py` (a separate dataclass with `defra_id, level1..4, column_text, uom, ghg_unit, row_number, sheet_name, metadata: dict`). Verified persistence path:

* `exporter.generate_sql()` → `_insert_statement()` writes **only** `(reporting_year, activity_type, co2e_multiplier, unit, scope, factor_source, factor_set, country, updated_at)`.
* `exporter.load_to_db()` (psycopg2) and `load_with_supabase()` write the **same 8 columns**; neither touches `import_batches` nor sets `import_batch_id`.
* `exporter.write_json()` serialises `as_dict()` **including `metadata`** into `output/json/emission_factors.json`.

**Therefore:** metadata is retained **only in the exported JSON artifact and in-memory during an import run** — it is **never persisted to the database**.

**E. Is there a database column for per-factor metadata?** **No.** `emission_factors` has no JSONB/JSON/text metadata column (`region_deprecated` is a legacy varchar and not usable). The natural-key index, CHECKs and FK are as previously documented.

**F. Does SEAI need per-factor DB metadata for v1?** Nice-to-have, not required. Mapping of needs → current storage:

| Need | v1 storage |
|---|---|
| Source row (published row fidelity) | JSON export artifact + batch provenance (checksum, source file) |
| Notes (LPG blend, wood moisture, milled-peat note) | Batch `notes`/`errors` JSONB + label suffix where meaningful; per-factor notes not storable today |
| Provisional status (2025) | `factor_set='SEAI-2025'` + batch provenance note; per-factor flag not storable today |
| NCV/GCV basis | Canonical label (`Natural gas (NCV)`) + batch methodology note |
| CO2-only semantics | `factor_source='SEAI'`, `factor_set='SEAI-2025'`, label suffix `(kg CO2)`, batch note |
| Conversion values (MJ/kg, density, PE) | Batch provenance + optional JSON export; not needed at runtime |
| SEAI methodology | Batch provenance + import report |

**G. Recommendation:** (1) **batch-level provenance is sufficient for v1** — create one `import_batches` row carrying provider/version/checksum/notes; (2) encode what fits in existing fields (source, set, scope, label suffix); (3) a per-factor metadata (JSONB) column would be a **future, separate schema decision** and is **not required** for SEAI v1. **Do not add a metadata column now.**

---

## 3. CO2 vs CO2e Finding

**A. Does the application assume every `co2e_multiplier` is full CO2e?** The naming does, but nothing enforces it:
* Column name: `emission_factors.co2e_multiplier`; domain field docstring: "Emissions per unit of consumption (kg CO2e)".
* Calculation engine: `quantity × co2e_multiplier` (unit-equality guard), snapshot field `co2e_kg`, emissions-log column `calculated_kg_co2e`. No code converts CO2↔CO2e or validates gas coverage — the multiplier is treated as an opaque numeric.

**B. Is `factor_source`/`factor_set` available downstream?** Yes, on the factor itself and on snapshots: `CalculationSink.save_snapshot(..., factor_source=None, factor_set=None, import_batch_id=None)` persists these to `calculation_snapshots`. The audit trail and `import_batches` also carry provider/source. So a SEAI factor is distinguishable by `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `provider_key='seai'`.

**C. Can a SEAI factor be stored in `co2e_multiplier` without false "full CO2e" representation?** For the **storage and calculation layers: yes** — the numeric value is exactly the multiplier used (`kg CO2` per unit). The risk is only in **labeling**: any output that renders the column name ("CO2e") verbatim would mislabel SEAI's CO2-only factors.

**D. Where should CO2-only semantics be preserved?** (in order of authority)
1. `import_batches` provenance: `provider_key='seai'`, `provider_version='2025 (V1.7)'`, batch note stating "CO2-only factors (CH4/N2O not published)".
2. `factor_source='SEAI'` + `factor_set='SEAI-2025'` on every factor.
3. Activity-label suffix `(kg CO2)` (mirrors DEFRA's `(kg CO2e ...)` grammar, so labels are honest).
4. Scope and methodology notes in the batch report / JSON export.

**E. Can this be done entirely through existing metadata/source/factor_set/batch mechanisms?** **Yes.** No schema or code change is needed to preserve the semantics; it is a labelling/provenance discipline.

**F. Would any current customer-facing output incorrectly label SEAI CO2 as CO2e?** **No current output surface exists** — the Phase 10 API/reporting/dashboard layers are not implemented (backend v2.1 stops at engines + repositories). When those phases render `co2e_kg`, they must branch on `factor_source` (available on the snapshot) to label SEAI correctly as CO2. **This is a documented non-blocking risk for v1, and a requirement to record for Phase 10** — not a blocker for the import.

**Recommendation:** store SEAI values in `co2e_multiplier`; enforce the labelling discipline in §3.D; file a Phase-10 requirement that reporting distinguishes CO2-only (SEAI) from CO2e (DEFRA) using `factor_source`.


---

## 4. Electricity Factor Representation Decision

**Evidence from the existing dataset:** the 7,029 DEFRA factors contain **no plain grid-electricity consumption factor** — the only `electric*` labels are EV/T&D categories (`UK electricity for EVs > ...`, `UK electricity T&D for EVs > ...`) and WTT rows. The established taxonomy grammar is `Fuels > <family> > <fuel> (kg CO2e of <species> per unit) [<unit>]` (e.g. `Fuels > Gaseous fuels > Natural gas (100% mineral blend) (kg CO2e of CO2 per unit) [cubic metres]`). DEFRA distinguishes GCV/NCV via **unit strings** (`kWh (Gross CV)` / `kWh (Net CV)`).

**SEAI electricity has no DEFRA label to mirror**, so the following canonical labels are proposed (approved as a condition in §10) using the `Fuels > ...` hierarchy and the `(kg CO2) [unit]` suffix:

| Family | Proposed `activity_type` | Unit | Scope | Multiplier (2025) |
|---|---|---|---|---|
| Electricity consumption | `Fuels > Electricity > Electricity consumption (kg CO2) [kWh]` | `kWh` | `Scope 2` (SEAI bundles T&D losses + own-use = Scope 3 in this factor — recorded in batch/metadata note) | `0.197803` kg CO2/kWh |
| Gross electricity supply | `Fuels > Electricity > Gross electricity supply (kg CO2) [kWh]` | `kWh` | `Scope 2` (generation; excludes imports) | `0.178328` kg CO2/kWh |

**A–G answers:**
- **A/B/C (labels/unit/scope):** as above. Unit `kWh` (existing canonical unit). Scope `Scope 2` for both, with the SEAI methodology nuance in the batch note.
- **D (matching distinguishes them):** distinct `activity_type` labels → exact/natural-key/keyword matching returns the correct family; `country='IE'` and `unit='kWh'` narrow candidates. A query for "electricity" without more context returns **both** → the existing pipeline returns `ambiguous`/`suggestions`.
- **E (alias risk):** yes — a generic alias `electricity → Electricity consumption` could mask the gross-supply factor. **Mitigation:** seed the alias explicitly to the **consumption** family (the standard reporting choice) with `target_provider_key='seai'`, and keep gross-supply reachable by its full label. Do **not** seed a bare `electricity` global alias until the ambiguity behaviour is exercised in tests.
- **F (import both for v1):** **Yes** — both are published SEAI 2025 factors with distinct methodologies; both should be imported.
- **G (special/provider-specific):** neither is "special" in the model — they are two ordinary factors. The consumption factor is the **default/primary** (alias target); gross supply is for generation-only reporting. No schema flag exists or is needed.


---

## 5. Exact 28-Source-Row → Factor Mapping (SEAI 2025 main sheet, sheet `Conversion and emission factors`, rows 22–65)

Conventions: `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `country='IE'`, `reporting_year=2025`, basis NCV unless noted, **CO2-only**. Multipliers are the published derived per-physical-unit values (kg CO2 per unit). Canonical labels follow the DEFRA grammar `Fuels > <family> > <name> (kg CO2) [<unit>]`.

### Imported — 20 records

| # | Source row | SEAI name | Section | Canonical `activity_type` | Unit | Multiplier (kg CO2/unit) | Basis | Scope | Provisional / Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | R22 | Crude oil | Liquid–Petroleum | `Fuels > Liquid fuels > Crude oil (kg CO2) [litres]` | `litres` | 2.942558 | kgCO2/l | Scope 1 | — |
| 2 | R23 | Gasoline / petrol (100% petroleum) | Liquid–Petroleum | `Fuels > Liquid fuels > Gasoline / petrol (100% petroleum) (kg CO2) [litres]` | `litres` | 2.310723 | kgCO2/l | Scope 1 | — |
| 3 | R24 | Kerosene | Liquid–Petroleum | `Fuels > Liquid fuels > Kerosene (kg CO2) [litres]` | `litres` | 2.524114 | kgCO2/l | Scope 1 | — |
| 4 | R25 | Jet Kerosene | Liquid–Petroleum | `Fuels > Liquid fuels > Jet Kerosene (kg CO2) [litres]` | `litres` | 2.518614 | kgCO2/l | Scope 1 | — |
| 5 | R26 | Diesel / gasoil (100% petroleum) | Liquid–Petroleum | `Fuels > Liquid fuels > Diesel / gasoil (100% petroleum) (kg CO2) [litres]` | `litres` | 2.682327 | kgCO2/l | Scope 1 | — |
| 6 | R27 | Residual fuel oil / fuel oil | Liquid–Petroleum | `Fuels > Liquid fuels > Residual fuel oil / fuel oil (kg CO2) [litres]` | `litres` | 2.951349 | kgCO2/l | Scope 1 | — |
| 7 | R28 | LPG | Liquid–Petroleum | `Fuels > Liquid fuels > LPG (kg CO2) [litres]` | `litres` | 1.568335 | kgCO2/l | Scope 1 | Note: 70% propane / 30% butane by mass |
| 8 | R32 | Biodiesel ME | Liquid–Biofuel | `Fuels > Liquid fuels > Biodiesel ME (kg CO2) [litres]` | `litres` | 0.133294 | kgCO2/l | Scope 1 | 5.4% fossil carbon (EPA NIS 2025) |
| 9 | R39 | Road diesel (avg. biofuel content) | Liquid–Blended | `Fuels > Liquid fuels > Road diesel (avg. biofuel content) (kg CO2) [litres]` | `litres` | 2.410411 | kgCO2/l | Scope 1 | Average 2025 blend |
| 10 | R40 | Road petrol (avg. biofuel content) | Liquid–Blended | `Fuels > Liquid fuels > Road petrol (avg. biofuel content) (kg CO2) [litres]` | `litres` | 2.085857 | kgCO2/l | Scope 1 | Average 2025 blend |
| 11 | R45 | Petroleum coke | Solid–Fossil | `Fuels > Solid fuels > Petroleum coke (kg CO2) [kg]` | `kg` | 2.988402 | kgCO2/kg | Scope 1 | **Provisional 2025** |
| 12 | R46 | Bituminous coal | Solid–Fossil | `Fuels > Solid fuels > Bituminous coal (kg CO2) [kg]` | `kg` | 2.633874 | kgCO2/kg | Scope 1 | — |
| 13 | R47 | Anthracite | Solid–Fossil | `Fuels > Solid fuels > Anthracite (kg CO2) [kg]` | `kg` | 2.736881 | kgCO2/kg | Scope 1 | — |
| 14 | R48 | Lignite | Solid–Fossil | `Fuels > Solid fuels > Lignite (kg CO2) [kg]` | `kg` | 2.001402 | kgCO2/kg | Scope 1 | — |
| 15 | R49 | Milled peat | Solid–Fossil | `Fuels > Solid fuels > Milled peat (kg CO2) [kg]` | `kg` | 0.741213 | kgCO2/kg | Scope 1 | Last used 2023; 2025 uses 2023 value |
| 16 | R50 | Sod peat | Solid–Fossil | `Fuels > Solid fuels > Sod peat (kg CO2) [kg]` | `kg` | 1.362887 | kgCO2/kg | Scope 1 | — |
| 17 | R51 | Peat briquettes | Solid–Fossil | `Fuels > Solid fuels > Peat briquettes (kg CO2) [kg]` | `kg` | 1.833608 | kgCO2/kg | Scope 1 | — |
| 18 | R60 | Natural gas (NCV) | Gas | `Fuels > Gaseous fuels > Natural gas (NCV) (kg CO2) [cubic metres]` | `cubic metres` | 2.005357 | kgCO2/m³ | Scope 1 | **Provisional 2025**; NCV basis |
| 19 | R64 | Electricity consumption | Electricity | `Fuels > Electricity > Electricity consumption (kg CO2) [kWh]` | `kWh` | 0.197803 | kgCO2/kWh | Scope 2 | Provisional 2025; bundles T&D losses + own-use (Scope 3 per SEAI note) |
| 20 | R65 | Gross electricity supply | Electricity | `Fuels > Electricity > Gross electricity supply (kg CO2) [kWh]` | `kWh` | 0.178328 | kgCO2/kWh | Scope 2 | Provisional 2025; generation, excludes imports |

### Skipped — 8 records

| # | Source row | SEAI name | Section | Reason |
|---|---|---|---|---|
| 21 | R31 | Bioethanol | Liquid–Biofuel | `no_factor_value` — biogenic net-zero; no CO2 factor published |
| 22 | R33 | Biodiesel HVO | Liquid–Biofuel | `no_factor_value` — biogenic net-zero |
| 23 | R34 | Biodiesel CHVO | Liquid–Biofuel | `no_factor_value` — biogenic net-zero |
| 24 | R35 | Biopropane | Liquid–Biofuel | `no_factor_value` — biogenic net-zero |
| 25 | R36 | Biojet HVO | Liquid–Biofuel | `no_factor_value` — biogenic net-zero |
| 26 | R54 | Wood pellets & briquettes | Solid–Biomass | `no_factor_value` — biogenic net-zero |
| 27 | R55 | Wood logs & chips | Solid–Biomass | `no_factor_value` — biogenic net-zero (25% moisture note) |
| 28 | R59 | Natural gas (GCV) | Gas | `non_canonical_basis` — GCV variant; physical-unit factor (kgCO2/m³) is identical to the NCV row (2.005357) and SEAI's canonical basis is NCV. Recorded in batch provenance; do not import a duplicate |

**Correction note:** the prior assessment's "8 skipped" count included Biodiesel ME (which DOES carry a value, 0.133294 kgCO2/l). Verified against the workbook: 7 no-value rows + 1 GCV variant = **8 skipped, 20 imported**.


---

## 6. Canonical Unit Decision

**Verified existing canonical unit strings** (distinct `unit` values present in the 7,029 DEFRA rows): `cubic metres`, `GJ`, `kg`, `km`, `kWh`, `kWh (Gross CV)`, `kWh (Net CV)`, `litres`, `miles`, `million litres`, `passenger.km`, `per FTE Working Hour`, `Room per night`, `tonne.km`, `tonnes`.

**Engine contract (critical):** `EmissionFactor.calculate_emissions(quantity, quantity_unit)` raises `UnitMismatchError` unless `quantity_unit == factor.unit` **exactly** (string equality). Therefore `factor.unit` must be the **quantity input unit** the user supplies — after canonicalisation this is also the factor source unit. There is no unit normalisation layer in the runtime path.

**Decision — reuse existing DEFRA unit strings; do not invent new ones:**

| SEAI factor family | Canonical unit | Notes |
|---|---|---|
| Liquid fuels | `litres` | NOT `l`; matches DEFRA `litres` |
| Solid fuels | `kg` (optionally `tonnes` = ×1000 for v2) | matches DEFRA `kg`/`tonnes` |
| Gas (natural gas) | `cubic metres` | NOT `m3`/`m³`/`m^3`; matches DEFRA `cubic metres` |
| Electricity | `kWh` | matches DEFRA `kWh` |

**Recommended v1 scope:** one canonical physical-unit factor per fuel (litres / kg / cubic metres / kWh) exactly as in the §5 table. Energy-basis variants (`kWh (Gross CV)` / `kWh (Net CV)`, `GJ`) are optional v2 additions — if added they must reuse the existing DEFRA unit strings.

---

## 7. Import-Batch Behaviour (verified against actual code/data)

| Question | Finding |
|---|---|
| A. How is `import_batches` created? | Via `data/imports.py` `ImportsRepository.create_batch(...)` (provider, version, year, source, checksum, created_by). The **DEFRA CLI importer never calls it** — batch rows exist only from integration tests. |
| B. Is `emission_factors.import_batch_id` populated? | **No.** Verified live: **all 7,029 DEFRA rows have `import_batch_id = NULL`**. The loaders (`load_to_db`, `load_with_supabase`) write only the 8 factor columns. |
| C. How is `provider_key` propagated? | The repository derives it via `LEFT JOIN import_batches ib ON ib.id = ef.import_batch_id` (`_FACTOR_COLUMNS`). With `import_batch_id = NULL`, `provider_key` resolves to `''` — **the current DEFRA factors have no provider linkage in the DB**. |
| D. How is `provider_version` represented? | `import_batches.provider_version` (e.g. `2025.1`); not stored on factors. |
| E. Idempotency | Natural-key upsert (`save()` `ON CONFLICT ... DO UPDATE`; SQL artifact `INSERT ... WHERE NOT EXISTS`). Re-runs update/insert nothing new. |
| F. Duplicate detection | Unique index `(reporting_year, activity_type, country, unit, scope)` + validator duplicate detection within a run. |
| G. Rollback | `ImportsRepository.rollback_batch` (status → `rolled_back`, `rolled_back_from` chain, deactivate) — not exercised by the DEFRA CLI loader. |
| H. `rows_imported/rows_skipped/rows_duplicate` | Fields exist on `import_batches` and are set by `complete_batch(...)`; the DEFRA loader does not call it (its counts live only in `ImportResult`/summary). |

**Why the 7,029 rows have `import_batch_id = NULL`:** the DEFRA importer predates/does not use the batch integration; migration M2's own checklist states "Existing 7029 rows untouched; import_batch_id = NULL". The batch integration exists in the data layer and migrations but was never wired into the DEFRA CLI loader.

**SEAI recommendation:** the SEAI importer **should** create one `import_batches` row (`provider_key='seai'`, `provider_version='2025 (V1.7)'`, `source_file`, SHA-256 checksum, `rows_total=28`, `rows_imported=20`, `rows_skipped=8`, `rows_duplicate=0`) and set `import_batch_id` on each imported factor **via the repository loader** (`EmissionFactorsRepository.save` supports `import_batch_id`). This is the only way `provider_key='seai'` is correctly derived and SEAI provenance is recorded. A batch-less static SQL artifact (like DEFRA's) would repeat the NULL-linkage gap — acceptable only if explicitly intended.


---

## 8. Natural-Key Assessment

Current unique index: `(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))`. Provider/source/set are NOT in the key.

**A. DEFRA GB + SEAI IE is safe.** Confirmed: every SEAI row is `country='IE'`; every DEFRA row is `country='GB'`; the key includes `country`, so no natural-key collision is possible between the two providers even with identical activity/unit/scope. The proposed SEAI labels are also distinct from all 7,029 DEFRA labels in practice, but the country dimension alone already guarantees safety.

**B. SEAI IE + a future same-country provider (e.g. EPA IE) could collide** if that provider publishes the same `(year, activity_type, country, unit, scope)`. This is a documented future limitation; no current dataset triggers it.

**C. Can SEAI labels be chosen without artificial provider-specific prefixes?** **Yes.** The §5 labels are natural SEAI names under the existing `Fuels > ...` grammar — no `SEAI-` prefix, no artificial disambiguator. They are collision-safe against DEFRA via the `country` dimension. (The `(kg CO2)` suffix is a *semantic* label, not a database workaround — it is the honest equivalent of DEFRA's `(kg CO2e ...)`.)

**Decision:** **Do not change the unique index for SEAI v1** — no collision exists or is demonstrated. Document the future same-country multi-provider limitation (a later migration to add provider/source to the unique index would be a deliberate, separate decision if/when a second IE provider is added).

---

## 9. Required Implementation Constraints (for the SEAI provider)

1. **Single-source rule:** read factors only from the main sheet `Conversion and emission factors` (2025 values); treat `Energy content / Emission factors / Density / Primary energy timeseries`, `road_petrol_blend`, `road_diesel_blend`, `GHG_elec` and `QAQC` as reference-only. This prevents duplicates from the blend/GHG sheets.
2. **Read cached values:** load with `openpyxl(data_only=True)`; verify a cached value exists for every imported cell (formula cells without cached values must fail validation, not guess).
3. **Populate per-row:** `country='IE'`, `factor_source='SEAI'`, `factor_set='SEAI-2025'`, `reporting_year=2025`, `provider_key='seai'` (via batch), scope per §5, canonical unit per §6, `(kg CO2) [unit]` label suffix.
4. **Create an `import_batches` row** (`provider_key='seai'`, `provider_version='2025 (V1.7)'`, source path + SHA-256 `e64f4f91…`, `rows_total=28`, `rows_imported=20`, `rows_skipped=8`, `rows_duplicate=0`) and **set `import_batch_id`** on every imported factor through the repository loader.
5. **Skip rule:** rows 21–28 per §5 (7 `no_factor_value` + 1 `non_canonical_basis` GCV) with explicit reasons; never import the same physical-unit factor from two sheets.
6. **Electricity:** import both families; seed the alias `electricity → Fuels > Electricity > Electricity consumption (kg CO2) [kWh]` with `target_provider_key='seai'`; leave gross supply reachable by full label; verify ambiguity behaviour in tests before adding a bare global alias.
7. **Validation gates:** non-negative multipliers; unit ∈ canonical set; duplicate detection by natural key within the run; report counts.
8. **Import target:** development against `carbontally_test` only; authoritative DB only after approval (idempotent upsert by natural key; DEFRA 7,029 must remain untouched).
9. **No engine/schema changes:** reuse `EmissionFactorsRepository`, `ImportsRepository`, `FactorMatchingEngine`, `CalculationEngine` unchanged.

---

## 10. Blockers

**No hard blockers.** The following are classification checks performed against actual code:

* CO2-vs-CO2e indistinguishability **would** be a blocker if any customer-facing output rendered `co2e_multiplier`/`co2e_kg` verbatim — **no such output exists** (Phase 10 API/reporting not implemented), and `factor_source` is available on factors and snapshots, so the distinction is preservable. **Not a blocker.**
* Per-factor metadata persistence gap — covered by batch-level provenance for v1. **Not a blocker.**
* No schema/migration/test-isolation issues. **Not a blocker.**


---

## 11. Non-Blocking Risks

| Risk | Severity | Mitigation / Owner |
|---|---|---|
| CO2-only factors rendered as "CO2e" in future API/reporting | Medium (future) | Phase-10 requirement: branch labels on `factor_source`/`factor_set` (available on snapshots); label SEAI as kg CO2 |
| Per-factor notes not storable (LPG mix, wood moisture, provisional flags) | Low | Batch provenance + JSON export artifact; optional future metadata column decision |
| Generic "electricity" matching ambiguity (consumption vs gross supply) | Low | Explicit alias to consumption family; ambiguity tests before any bare global alias |
| GCV/NCV duplicate risk (identical kgCO2/m³) | Low | Single-source rule + skip GCV variant (documented) |
| Energy-basis kWh factors absent in v1 (users entering kWh of fuel energy) | Low–Medium | v2 addition using `kWh (Net CV)`/`kWh (Gross CV)`/`GJ` canonical units |
| Batch-linkage gap if SEAI uses a batch-less SQL artifact (like DEFRA) | Medium | Constraint §9.4 — SEAI must use the repository loader with `import_batch_id` |
| Provisional 2025 values (petroleum coke, gas, electricity, milled peat) | Low | Recorded in batch provenance; re-import when SEAI publishes final values (idempotent upsert) |
| Milled peat discontinued (2023 values reused) | Low | Note in provenance; label retains SEAI name |
| Future same-country multi-provider (SEAI + EPA IE) natural-key collision | Low (future) | Documented; later migration decision if a second IE provider is added |

---

## 12. Exact Recommended Implementation Sequence

1. Approve this gate (conditions in §10/§9).
2. Approve the exact 28-row mapping table (§5), canonical units (§6), and electricity labels (§4).
3. Implement SEAI provider plugin under `src/providers/seai/` mirroring `src/providers/defra/` (reader → parser → normalizer → mapper → validator → exporter/loader).
4. Implement the SEAI importer CLI (mirror `src/commands/import_defra.py`) with the **repository loader that creates an `import_batches` row and sets `import_batch_id`**.
5. Add SEAI fixture tests (parser/mapper/validator/loader against the workbook).
6. Import SEAI 2025 into `carbontally_test`; assert 20 imported / 8 skipped, natural-key uniqueness, batch provenance.
7. Validate matching (exact/natural-key/alias/keyword/fuzzy/ambiguous/no-match; UK-vs-Ireland provider isolation; electricity ambiguity).
8. Validate calculations (unit equality, snapshot, content hash, audit/events) with SEAI factors.
9. Run the DEFRA regression suite (7,029 factors intact) + unit suite + mypy --strict + compile/arch checks.
10. After approval, import into the authoritative database (idempotent upsert by natural key; DEFRA untouched).
11. Verify final counts (DEFRA 7,029 + SEAI 20 for 2025) and provenance.
12. Record the Phase-10 CO2-vs-CO2e labelling requirement.

---

## Final Verdict

The four gate questions are resolved: metadata is not persisted per-factor today (batch provenance suffices for v1); CO2-only semantics are preservable via existing source/set/scope/label/batch fields with no current output mislabelling them; the two electricity families map cleanly to two ordinary factors with unambiguous labels; and the exact 28→20 mapping with canonical units is defined. DEFRA-GB + SEAI-IE are collision-safe through the `country` dimension; no unique-index change is required.

**Conditions to satisfy before (and during) implementation** (design approvals only — no schema or engine changes): (1) approve the §5 mapping / §6 units / §4 electricity labels; (2) SEAI importer must create an `import_batches` row and set `import_batch_id` (repository loader, not a batch-less SQL artifact); (3) approve the CO2-only labelling discipline (§3.D) and record the Phase-10 rendering requirement; (4) follow the single-source import rule and skip rule (§5, §9).

GO WITH CONDITIONS — IMPLEMENT ONLY AFTER CONDITIONS ARE SATISFIED

