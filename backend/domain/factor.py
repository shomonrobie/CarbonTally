"""Emission-factor domain objects (Backend v2.1 §9, ADR-10).

Pure Python. No framework, database or infrastructure imports. Every object is
an immutable frozen dataclass; state changes produce new instances.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Optional

from core.exceptions import UnitMismatchError

#: Result precision for calculated emissions (kg CO2e, 6 decimal places).
RESULT_PRECISION = Decimal("0.000001")


def gas_coverage(factor: EmissionFactor) -> str:
    """Return ``"CO2"`` for CO2-only factors (SEAI) and ``"CO2e"`` otherwise.

    SEAI publishes CO2-only emission factors (CH4/N2O excluded by source
    design) while DEFRA publishes CO2e. The distinction is preserved through
    ``factor_source`` and the ``(kg CO2)`` activity-label suffix — never
    through the schema. Validation, benchmarking and reporting engines use
    this to avoid labelling CO2-only data as full CO2e.
    """
    if factor.factor_source == "SEAI":
        return "CO2"
    if "(kg CO2)" in factor.activity_type:
        return "CO2"
    return "CO2e"


@dataclass(frozen=True, slots=True)
class EmissionFactor:
    """An emission factor as stored in the RC2 ``emission_factors`` table.

    Attributes:
        id: Primary key (UUID string).
        reporting_year: The reporting year the factor applies to.
        activity_type: RC2 activity label (e.g.
            ``Fuels > Liquid fuels > Diesel ... (kg CO2e) [litres]``).
        co2e_multiplier: Emissions per unit of consumption (kg CO2e).
        unit: Unit the multiplier applies to (``None`` when unpublished).
        scope: GHG Protocol scope label, or ``None``.
        factor_source: Source authority (e.g. ``DEFRA-DESNZ``).
        factor_set: Named vintage/set (e.g. ``DEFRA-2025``).
        country: Jurisdiction (``GB``, ``IE``, ...).
        provider_key: Provider plugin identifier (``defra``, ``seai``, ...).
        import_batch_id: Import batch that created this factor (nullable for
            pre-existing rows).
        natural_key: RC2 natural key
            ``(reporting_year, activity_type, country, unit, scope)``.
    """

    id: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: Decimal
    unit: Optional[str] = None
    scope: Optional[str] = None
    factor_source: str = ""
    factor_set: str = ""
    country: str = "GB"
    provider_key: str = ""
    import_batch_id: Optional[str] = None
    natural_key: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.co2e_multiplier < 0:
            raise ValueError("co2e_multiplier must be >= 0")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.activity_type:
            raise ValueError("activity_type must not be empty")

    def calculate_emissions(self, quantity: Decimal, quantity_unit: str) -> Decimal:
        """Compute kg CO2e for a quantity expressed in the factor's unit.

        Args:
            quantity: Consumption quantity (must be >= 0).
            quantity_unit: Unit of the consumption quantity.

        Returns:
            ``quantity * co2e_multiplier`` rounded to 6 decimal places.

        Raises:
            UnitMismatchError: When ``quantity_unit`` differs from the factor's
                unit (a factor without a unit accepts any unit).
            ValueError: When ``quantity`` is negative.
        """
        if self.unit is not None and quantity_unit != self.unit:
            raise UnitMismatchError(
                f"consumption unit {quantity_unit!r} does not match factor "
                f"unit {self.unit!r} for factor {self.id}"
            )
        if quantity < 0:
            raise ValueError("quantity must be >= 0")
        return (quantity * self.co2e_multiplier).quantize(RESULT_PRECISION)

    def with_new_year(self, year: int) -> EmissionFactor:
        """Return a copy of this factor for a different reporting year.

        Args:
            year: The new reporting year.

        Returns:
            A new :class:`EmissionFactor` sharing all other attributes.
        """
        return replace(self, reporting_year=year)


@dataclass(frozen=True, slots=True)
class FactorSetMetadata:
    """Provenance metadata for a complete factor set."""

    row_count: int
    checksum: str
    imported_at: datetime
    source_path: str


@dataclass(frozen=True, slots=True)
class FactorSet:
    """A complete set of factors for one provider, year and version."""

    provider_key: str
    reporting_year: int
    version: str
    factors: tuple[EmissionFactor, ...] = ()
    metadata: Optional[FactorSetMetadata] = None

    def find_by_natural_key(self, key: tuple[str, ...]) -> Optional[EmissionFactor]:
        """Return the factor with the given natural key, or ``None``."""
        return next((f for f in self.factors if f.natural_key == key), None)

    def search_by_activity(
        self, activity: str, unit: Optional[str] = None
    ) -> list[EmissionFactor]:
        """Return factors whose activity type contains ``activity`` (case-insensitive).

        When ``unit`` is supplied the results are narrowed to factors with that
        unit. Matching is substring based — ranking is the Matching Platform's
        responsibility.
        """
        needle = activity.casefold()
        matches = [f for f in self.factors if needle in f.activity_type.casefold()]
        if unit is not None:
            matches = [f for f in matches if f.unit == unit]
        return matches
