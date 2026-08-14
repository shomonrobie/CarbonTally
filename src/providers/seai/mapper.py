"""SEAI mapper (CarbonTally SEAI 2025 provider).

Maps the parsed authoritative-sheet rows onto canonical CarbonTally factors per
the approved Implementation Gate v1.0 mapping:

* Only the final per-physical-unit emission factors become factors. The
  workbook publishes these directly (kgCO2/l for liquids, kgCO2/kg for solids,
  kgCO2/m^3 for gas, gCO2/kWh for electricity) — the mapper selects the
  canonical column per section.
* Electricity gCO2/kWh is converted to the canonical kg CO2/kWh multiplier.
* Rows without a published numeric emission factor (biogenic net-zero
  biofuel/biomass rows) are skipped with ``no_factor_value``.
* ``Natural gas (GCV)`` is skipped with ``non_canonical_basis``: SEAI's
  canonical basis is NCV, and the GCV row's physical-unit factor (kgCO2/m^3)
  is identical to the NCV row, so importing it would create a duplicate.

Canonical conventions (from the gate):
* activity label: ``Fuels > <family> > <name> (kg CO2) [<unit>]``
* family from section: Liquid fuels | Solid fuels | Gaseous fuels | Electricity
* scope: Scope 1 (fuels) | Scope 2 (electricity)
* country IE, factor_source SEAI, factor_set SEAI-2025, reporting_year 2025
* CO2-only semantics preserved via the ``(kg CO2)`` label suffix + provider
  fields (not via any schema change).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .models import (
    COUNTRY,
    FACTOR_SET,
    FACTOR_SOURCE,
    PROVIDER_KEY,
    REPORTING_YEAR,
    SECTION_FAMILY,
    SECTION_SCOPE,
    SECTION_UNIT,
    SKIP_NON_CANONICAL_BASIS,
    SKIP_NO_FACTOR_VALUE,
    SeaiFactor,
    SeaiParsedRow,
    SeaiSkip,
)

#: Activity names that carry the "Provisional values for 2025" flag.
PROVISIONAL_NAMES = {"Petroleum coke", "Natural gas (NCV)", "Natural gas (GCV)"}

#: Natural gas GCV row is non-canonical (duplicate physical-unit factor).
_GAS_GCV_NAME = "Natural gas (GCV)"
_GAS_NCV_NAME = "Natural gas (NCV)"

#: Published precision on the authoritative sheet (6 decimal places). The
#: electricity factors are published in gCO2/kWh rounded to 6 dp and are
#: converted to kg CO2/kWh (0.197803384 / 0.178327674 per the approved gate).
_FACTOR_PRECISION = Decimal("0.000001")


def _natural_key(factor: SeaiFactor) -> tuple[str, ...]:
    """RC2 natural key ``(year, activity, country, unit, scope)``."""
    return (
        str(factor.reporting_year),
        factor.activity_type,
        factor.country or "GB",
        factor.unit or "{no-unit}",
        factor.scope or "{no-scope}",
    )


def _canonical_label(name: str, family: str, unit: str) -> str:
    return f"Fuels > {family} > {name} (kg CO2) [{unit}]"


def _skip(row: SeaiParsedRow, reason: str, detail: str) -> SeaiSkip:
    return SeaiSkip(
        row_number=row.row_number,
        name=row.name,
        section=row.top_section,
        reason=reason,
        detail=detail,
    )


def _multiplier_for(row: SeaiParsedRow) -> tuple[Optional[Decimal], str]:
    """Return ``(multiplier, basis)`` for the canonical physical-unit factor."""
    if row.top_section == "Liquid":
        value = row.kgco2_per_l
        basis = "kgCO2/l"
    elif row.top_section == "Solid":
        value = row.kgco2_per_mass_unit
        basis = "kgCO2/kg"
    elif row.top_section == "Gas":
        value = row.kgco2_per_mass_unit
        basis = "kgCO2/m^3"
    elif row.top_section == "Electricity":
        if row.gco2_per_kwh is None:
            return None, "kgCO2/kWh"
        # Quantise the published grams value to 6 dp, then convert to kg so the
        # stored multiplier matches the published/approved figure exactly
        # (e.g. 197.803384 gCO2/kWh -> 0.197803384 kgCO2/kWh).
        grams = row.gco2_per_kwh.quantize(_FACTOR_PRECISION)
        return grams / Decimal("1000"), "kgCO2/kWh"
    else:
        return None, ""
    if value is None:
        return None, basis
    return value.quantize(_FACTOR_PRECISION), basis


def map_row(row: SeaiParsedRow) -> tuple[Optional[SeaiFactor], Optional[SeaiSkip]]:
    """Map one parsed row to a canonical factor or a skip record."""
    if row.name == _GAS_GCV_NAME:
        return None, _skip(
            row,
            SKIP_NON_CANONICAL_BASIS,
            "GCV variant; SEAI canonical basis is NCV and the physical-unit "
            "factor (kgCO2/m^3) is identical to the NCV row — importing it "
            "would create a duplicate.",
        )
    multiplier, basis = _multiplier_for(row)
    if multiplier is None:
        return None, _skip(
            row,
            SKIP_NO_FACTOR_VALUE,
            "No numeric emission factor published (biogenic carbon treated as "
            "net zero by SEAI).",
        )
    if multiplier < 0:
        return None, _skip(row, "invalid_factor", "Negative emission factor value.")
    unit = SECTION_UNIT[row.top_section]
    family = SECTION_FAMILY[row.top_section]
    factor = SeaiFactor(
        reporting_year=REPORTING_YEAR,
        activity_type=_canonical_label(row.name, family, unit),
        co2e_multiplier=multiplier,
        unit=unit,
        scope=SECTION_SCOPE[row.top_section],
        factor_source=FACTOR_SOURCE,
        factor_set=FACTOR_SET,
        country=COUNTRY,
        provider_key=PROVIDER_KEY,
        source_row=row.row_number,
        source_name=row.name,
        basis=basis,
        co2_only=True,
        provisional=row.name in PROVISIONAL_NAMES,
        note=row.note,
    )
    factor.natural_key = _natural_key(factor)
    return factor, None


def map_all(rows: list[SeaiParsedRow]) -> tuple[list[SeaiFactor], list[SeaiSkip]]:
    """Map every parsed row; returns ``(factors, skipped)``."""
    factors: list[SeaiFactor] = []
    skipped: list[SeaiSkip] = []
    for row in rows:
        factor, skip = map_row(row)
        if factor is not None:
            factors.append(factor)
        if skip is not None:
            skipped.append(skip)
    return factors, skipped
