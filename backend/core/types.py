"""Canonical primitive types for the CarbonTally platform (Backend v2.1 §9).

The domain layer deliberately models countries, scopes, units and years as
plain ``str``/``int`` fields (frozen contract) so new jurisdictions and
providers can be added without a domain change. The enums below define the
canonical vocabulary for the known values; because :class:`~enum.StrEnum`
subclasses ``str``, they can be used interchangeably wherever a ``str`` is
accepted. :class:`DateRange` is a value object used by repository contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import NewType

#: A consumption unit (free text — e.g. ``kWh``, ``litres``, ``tonnes``, ``km``).
Unit = NewType("Unit", str)

#: A reporting year (e.g. ``2025``).
ReportingYear = NewType("ReportingYear", int)


class Country(StrEnum):
    """ISO 3166-1 alpha-2 country codes currently supported by the platform."""

    GB = "GB"
    IE = "IE"


class Scope(StrEnum):
    """GHG Protocol scope vocabulary used by DEFRA-style factor datasets."""

    SCOPE_1 = "Scope 1"
    SCOPE_2 = "Scope 2"
    SCOPE_3 = "Scope 3"
    OUTSIDE_OF_SCOPES = "Outside of Scopes"


@dataclass(frozen=True, slots=True)
class DateRange:
    """An inclusive date range value object.

    Attributes:
        start_date: Inclusive start of the range.
        end_date: Inclusive end of the range (must be >= ``start_date``).
    """

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date {self.end_date.isoformat()} is before "
                f"start_date {self.start_date.isoformat()}"
            )

    def contains(self, day: date) -> bool:
        """Return ``True`` when ``day`` falls inside the range (inclusive)."""
        return self.start_date <= day <= self.end_date

    def overlaps(self, other: DateRange) -> bool:
        """Return ``True`` when this range shares at least one day with ``other``."""
        return self.start_date <= other.end_date and other.start_date <= self.end_date
