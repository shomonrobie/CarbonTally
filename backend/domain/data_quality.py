"""P17 data-quality classification (ARCH-01 data quality, P17-B..P17-I).

Pure Python. No framework, database or infrastructure imports.

Data quality is a statement about *how* a number was obtained. It is recorded
because the alternative — presenting every figure with the same implied
confidence — misleads the reader into treating an industry-average estimate as if
it were a metered reading.

The vocabulary is exactly five values and deliberately carries NO numeric
uncertainty. A percentage uncertainty band would be a fabricated precision: the
platform does not measure it, so it must not display it.

    primary_measured       metered/measured at source
    primary_supplier       declared by the supplier for this activity
    secondary_estimated    estimated from average/secondary data
    spend_based_estimated  derived from spend (economic intensity)
    modelled               produced by a model rather than measured

Three of them are ESTIMATES. An estimated value must carry a persisted estimation
record (T-INV-12), which is why :func:`is_estimated` exists and is the single
predicate the rest of the system uses.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Optional

from core.exceptions import AccountingDimensionError

__all__ = [
    "DataQuality",
    "DATA_QUALITY_VALUES",
    "ESTIMATED_DATA_QUALITY",
    "validate_data_quality",
    "is_estimated",
    "describe_data_quality",
]


class DataQuality(StrEnum):
    """The five data-quality classifications. No numeric uncertainty is implied."""

    PRIMARY_MEASURED = "primary_measured"
    PRIMARY_SUPPLIER = "primary_supplier"
    SECONDARY_ESTIMATED = "secondary_estimated"
    SPEND_BASED_ESTIMATED = "spend_based_estimated"
    MODELLED = "modelled"


#: Frozen vocabulary, matching the database CHECK constraint.
DATA_QUALITY_VALUES: tuple[str, ...] = tuple(q.value for q in DataQuality)

#: The subset that is an ESTIMATE and therefore requires an estimation record.
ESTIMATED_DATA_QUALITY: frozenset[str] = frozenset({
    DataQuality.SECONDARY_ESTIMATED.value,
    DataQuality.SPEND_BASED_ESTIMATED.value,
    DataQuality.MODELLED.value,
})

_DESCRIPTIONS: dict[str, str] = {
    DataQuality.PRIMARY_MEASURED.value:
        "Measured or metered at source.",
    DataQuality.PRIMARY_SUPPLIER.value:
        "Declared by the supplier or utility for this activity.",
    DataQuality.SECONDARY_ESTIMATED.value:
        "Estimated from secondary or industry-average data.",
    DataQuality.SPEND_BASED_ESTIMATED.value:
        "Derived from spend using an economic intensity factor.",
    DataQuality.MODELLED.value:
        "Produced by a model rather than measured or declared.",
}


def validate_data_quality(value: Optional[str]) -> Optional[str]:
    """Return ``value`` when it is a valid data-quality classification, else raise.

    ``None`` means "not classified". It is NOT silently treated as primary data:
    an unclassified value is a visible gap, not an implicit assurance.
    """
    if value is None:
        return None
    if value not in DATA_QUALITY_VALUES:
        raise AccountingDimensionError(
            f"invalid data quality {value!r}; expected one of {DATA_QUALITY_VALUES}",
            details={"field": "data_quality", "received": value,
                     "allowed": list(DATA_QUALITY_VALUES)},
        )
    return value


def is_estimated(value: Optional[str]) -> bool:
    """True when this classification is an estimate requiring an estimation record.

    This is the predicate the no-silent-estimation rule (T-INV-12) is built on.
    """
    return value in ESTIMATED_DATA_QUALITY


def describe_data_quality(value: Optional[str]) -> str:
    """Return a user-facing description suitable for an operational UI."""
    if value is None:
        return "Data quality not classified."
    return _DESCRIPTIONS.get(value, value)
