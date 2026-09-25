"""P17 data-quality classification (ARCH-01 data quality, P17-B..P17-I).

Pure Python. No framework, database or infrastructure imports.

Data quality is a statement about *how* a number was obtained. It is recorded
because the alternative — presenting every figure with the same implied
confidence — misleads the reader into treating an industry-average estimate as if
it were a metered reading.

The vocabulary deliberately carries NO numeric uncertainty. A percentage
uncertainty band would be a fabricated precision: the platform does not measure
it, so it must not display it.

The classifications, reconciled with the authoritative product contract
(P17-PRODUCT-01 §7) and its reporting requirement (§29 Reporting model, §30
Investor dashboard — "derived from actual data, not demo decoration"):

    primary_measured       metered/measured at source
    primary_supplier       declared by the supplier for this activity
    secondary_estimated    estimated from average/secondary data
    spend_based_estimated  derived from spend (economic intensity)
    modelled               produced by a model rather than measured
    activity_based         derived from an activity-based factor
    estimated              a labelled estimate with a persisted basis
    manual                 established by controlled human review
    unresolved             could not be determined and is carried as unknown

P17-PRODUCT-01 §7 introduces its list with "For example", so the four
product-facing classifications it names that P17-A could not express
(``ACTIVITY_BASED``, ``ESTIMATED``, ``MANUAL``, ``UNRESOLVED``) are added here
while the five P17-A values are preserved verbatim. The database CHECK is
widened to the same superset, never narrowed, so no stored row is invalidated.

Four of them are ESTIMATES. An estimated value must carry a persisted estimation
record (T-INV-12), which is why :func:`is_estimated` exists and is the single
predicate the rest of the system uses. ``activity_based`` is deliberately NOT an
estimate (it is activity data, §6 hierarchy step 4), and ``manual`` /
``unresolved`` are NOT estimates either — ``manual`` describes who established
the value, and ``unresolved`` is the explicit admission that no value was
established at all. Treating either as an estimate would silently invent an
estimation obligation the product contract does not impose.
"""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Mapping, Optional

from core.exceptions import AccountingDimensionError

__all__ = [
    "DataQuality",
    "DATA_QUALITY_VALUES",
    "ESTIMATED_DATA_QUALITY",
    "PRODUCT_DATA_QUALITY_BUCKETS",
    "validate_data_quality",
    "is_estimated",
    "describe_data_quality",
    "reporting_bucket",
    "describe_bucket",
    "quality_mix",
]


class DataQuality(StrEnum):
    """The data-quality classifications. No numeric uncertainty is implied."""

    PRIMARY_MEASURED = "primary_measured"
    PRIMARY_SUPPLIER = "primary_supplier"
    SECONDARY_ESTIMATED = "secondary_estimated"
    SPEND_BASED_ESTIMATED = "spend_based_estimated"
    MODELLED = "modelled"
    # --- P17-PRODUCT-01 §7 / §29 / §30 product classifications ---
    ACTIVITY_BASED = "activity_based"
    ESTIMATED = "estimated"
    MANUAL = "manual"
    UNRESOLVED = "unresolved"


#: Frozen vocabulary, matching the database CHECK constraint.
DATA_QUALITY_VALUES: tuple[str, ...] = tuple(q.value for q in DataQuality)

#: The subset that is an ESTIMATE and therefore requires an estimation record.
ESTIMATED_DATA_QUALITY: frozenset[str] = frozenset({
    DataQuality.SECONDARY_ESTIMATED.value,
    DataQuality.SPEND_BASED_ESTIMATED.value,
    DataQuality.MODELLED.value,
    DataQuality.ESTIMATED.value,
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
    DataQuality.ACTIVITY_BASED.value:
        "Derived from an activity-based factor.",
    DataQuality.ESTIMATED.value:
        "A labelled estimate carrying a persisted estimation basis.",
    DataQuality.MANUAL.value:
        "Established by controlled human review.",
    DataQuality.UNRESOLVED.value:
        "Not determined; carried as unknown rather than guessed.",
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


# ---------------------------------------------------------------------------
# Reporting projection (P17-PRODUCT-01 §29 "Reporting model" / §30 Investor
# dashboard)
# ---------------------------------------------------------------------------
#: The reporting buckets, in the order §30 presents them. This is a *projection*
#: of the stored vocabulary, not a second vocabulary: every persisted
#: classification maps onto exactly one bucket, deterministically, and the
#: mapping is total. §30 requires the mix to be "derived from actual data, not
#: demo decoration", which is what :func:`quality_mix` computes.
BUCKET_PRIMARY_DATA = "PRIMARY_DATA"
BUCKET_ACTIVITY_BASED = "ACTIVITY_BASED"
BUCKET_AVERAGE_DATA = "AVERAGE_DATA"
BUCKET_SPEND_BASED = "SPEND_BASED"
BUCKET_ESTIMATED = "ESTIMATED"
BUCKET_MANUAL_REVIEW = "MANUAL_REVIEW"
BUCKET_UNRESOLVED = "UNRESOLVED"
BUCKET_UNCLASSIFIED = "UNCLASSIFIED"

#: Ordered bucket names — §30's list, then the explicit unclassified bucket.
PRODUCT_DATA_QUALITY_BUCKETS: tuple[str, ...] = (
    BUCKET_PRIMARY_DATA,
    BUCKET_ACTIVITY_BASED,
    BUCKET_AVERAGE_DATA,
    BUCKET_SPEND_BASED,
    BUCKET_ESTIMATED,
    BUCKET_MANUAL_REVIEW,
    BUCKET_UNRESOLVED,
    BUCKET_UNCLASSIFIED,
)

#: Persisted classification -> reporting bucket. Total by construction: the
#: `.get(..., BUCKET_UNCLASSIFIED)` fallback means an unrecognised value can
#: never be dropped from a report, it is surfaced as unclassified.
_BUCKET_BY_VALUE: dict[str, str] = {
    # §33 Level 7 — "Primary data: supplier-specific / actual data".
    DataQuality.PRIMARY_MEASURED.value: BUCKET_PRIMARY_DATA,
    DataQuality.PRIMARY_SUPPLIER.value: BUCKET_PRIMARY_DATA,
    DataQuality.ACTIVITY_BASED.value: BUCKET_ACTIVITY_BASED,
    DataQuality.SECONDARY_ESTIMATED.value: BUCKET_AVERAGE_DATA,
    DataQuality.SPEND_BASED_ESTIMATED.value: BUCKET_SPEND_BASED,
    # `modelled` is a P17-A value with no §30 bucket of its own; it is an
    # estimate produced by a model, so it reports under Estimated rather than
    # being hidden. Documented, deterministic, and asserted by test.
    DataQuality.MODELLED.value: BUCKET_ESTIMATED,
    DataQuality.ESTIMATED.value: BUCKET_ESTIMATED,
    DataQuality.MANUAL.value: BUCKET_MANUAL_REVIEW,
    DataQuality.UNRESOLVED.value: BUCKET_UNRESOLVED,
}

_BUCKET_LABELS: dict[str, str] = {
    BUCKET_PRIMARY_DATA: "Primary data",
    BUCKET_ACTIVITY_BASED: "Activity based",
    BUCKET_AVERAGE_DATA: "Average data",
    BUCKET_SPEND_BASED: "Spend based",
    BUCKET_ESTIMATED: "Estimated",
    BUCKET_MANUAL_REVIEW: "Manual review",
    BUCKET_UNRESOLVED: "Unresolved",
    BUCKET_UNCLASSIFIED: "Not classified",
}


def reporting_bucket(value: Optional[str]) -> str:
    """Project a persisted classification onto its §29/§30 reporting bucket.

    ``None`` (not classified) maps to ``UNCLASSIFIED`` rather than being
    silently folded into a quality bucket: an unclassified value is a visible
    gap, and a report that hid it would overstate the quality of the data.
    """
    if value is None:
        return BUCKET_UNCLASSIFIED
    return _BUCKET_BY_VALUE.get(value, BUCKET_UNCLASSIFIED)


def describe_bucket(bucket: str) -> str:
    """Return the human-readable §30 label for a reporting bucket."""
    return _BUCKET_LABELS.get(bucket, bucket)


def quality_mix(counts: Mapping[str, int]) -> dict[str, object]:
    """Aggregate persisted classification counts into the §29/§30 data-quality mix.

    Args:
        counts: persisted ``data_quality`` value -> number of results carrying
            it. ``None`` is the not-classified key.

    Returns:
        ``{"buckets": {bucket: {"count", "label"}}, "total", "percentages"}``.
        Percentages are computed **only** when the total is non-zero; with no
        results at all every percentage is ``None`` rather than ``0`` or a
        division by zero, because "no data" and "0% of the data" are different
        statements and the report must not conflate them.
    """
    bucket_counts: dict[str, int] = {name: 0 for name in PRODUCT_DATA_QUALITY_BUCKETS}
    total = 0
    for value, count in counts.items():
        amount = int(count)
        if amount < 0:
            raise AccountingDimensionError(
                f"a data-quality count cannot be negative: {value!r} -> {count!r}"
            )
        # `None` is the not-classified key; any other key is projected.
        bucket = reporting_bucket(None if value in (None, "none", "") else str(value))
        bucket_counts[bucket] += amount
        total += amount

    percentages: dict[str, Optional[str]] = {}
    for name, amount in bucket_counts.items():
        if total == 0:
            percentages[name] = None
        else:
            # Two decimal places, from the authoritative counts only.
            percentages[name] = str(
                (Decimal(amount) * Decimal(100) / Decimal(total)).quantize(
                    Decimal("0.01")
                )
            )

    return {
        "buckets": {
            name: {"count": bucket_counts[name], "label": describe_bucket(name)}
            for name in PRODUCT_DATA_QUALITY_BUCKETS
        },
        "total": total,
        "percentages": percentages,
    }
