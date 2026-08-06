# Mapping Report

Reporting year: **2025**

## Worksheets containing emission factors

### `Factors by Category` (header row 6)

| Workbook column | Target DB field | Notes |
|---|---|---|
| `ID` | `defra_id` (reference only — no DB column) | |
| `Scope` | `scope` | |
| `Level 1` | `activity_type` (label component) | |
| `Level 2` | `activity_type` (label component) | |
| `Level 3` | `activity_type` (label component) | |
| `Level 4` | `activity_type` (label component) | |
| `Column Text` | `activity_type` (label component) | |
| `UOM` | `unit` | |
| `GHG/Unit` | `activity_type` (label component) | |
| `GHG Conversion Factor 2025` | `co2e_multiplier` (exact decimal, unrounded) | |

## Constant values applied

| DB field | Value |
|---|---|
| `reporting_year` | 2025 |
| `factor_source` | `DEFRA-DESNZ` |
| `factor_set` | `DEFRA-2025` |
| `country` | `GB` |

## Natural key (idempotency)

`(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))`