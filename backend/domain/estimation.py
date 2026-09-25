"""P17 estimation records and the no-silent-estimation rule (P17-H, T-INV-12).

Pure Python. No framework, database or infrastructure imports.

Invariant T-INV-12: an estimated value carries a persisted estimation record —
method, inputs, assumptions, factor, source, actor, timestamp.

The point of the invariant is that an estimate must be *inspectable*. "We
estimated it" is an assertion; an estimation record is evidence. Without one, a
reader cannot tell whether an estimate was a careful proxy or a placeholder, and
the platform must never present the two alike.

This module therefore refuses an estimate that names no method or records no
inputs and no assumptions. It does not require the estimate to be *good* — quality
is a judgement for a reviewer — only that it is *described*.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping, Optional

from core.exceptions import EstimationRecordRequiredError

from .data_quality import is_estimated

__all__ = [
    "EstimationMethod",
    "ESTIMATION_METHODS",
    "EstimationRecord",
    "validate_estimation_method",
    "assert_estimation_substantiated",
    "requires_estimation_record",
]


class EstimationMethod(StrEnum):
    """How the estimate was produced. Matches the database CHECK vocabulary."""

    AVERAGE_DATA = "average_data"
    PROXY_DATA = "proxy_data"
    SPEND_BASED = "spend_based"
    EXTRAPOLATED = "extrapolated"
    SUPPLIER_SPECIFIC = "supplier_specific"
    MODELLED = "modelled"
    INDUSTRY_AVERAGE = "industry_average"
    OTHER = "other"


#: Frozen vocabulary, matching the ``estimation_records_method_check`` constraint.
ESTIMATION_METHODS: tuple[str, ...] = tuple(m.value for m in EstimationMethod)


def validate_estimation_method(value: Optional[str]) -> str:
    """Return ``value`` when it is a recognised estimation method, else raise.

    Unlike the other dimension validators this does NOT accept ``None``: an
    estimation record without a method is exactly the unsubstantiated claim the
    invariant forbids.
    """
    if value is None:
        raise EstimationRecordRequiredError(
            "an estimation record must name its estimation method; a record that "
            "names no method does not substantiate the estimate (T-INV-12)",
            details={"field": "estimation_method", "allowed": list(ESTIMATION_METHODS)},
        )
    if value not in ESTIMATION_METHODS:
        raise EstimationRecordRequiredError(
            f"invalid estimation method {value!r}; expected one of {ESTIMATION_METHODS}",
            details={"field": "estimation_method", "received": value,
                     "allowed": list(ESTIMATION_METHODS)},
        )
    return value


@dataclass(frozen=True, slots=True)
class EstimationRecord:
    """The persisted evidence that a value is estimated.

    Attributes:
        organization_id: The organization that owns the estimated value.
        estimation_method: How the estimate was produced.
        inputs: The concrete inputs the estimate was computed from.
        assumptions: The assumption set the estimate rests on.
        calculation_snapshot_id: The result this record substantiates.
        emissions_log_id: The emissions row this record substantiates.
        factor_id: The factor used, when the estimate used one.
        source_reference: Where the source data came from.
        scope3_category: The category, when the estimate is category-scoped.
        actor_user_id: Who produced the estimate.
        actor_organization_id: The organization the actor belongs to.
        acting_for_organization_id: The organization the actor was operating for.
        created_at: When the record was created.
    """

    organization_id: str
    estimation_method: str
    inputs: Mapping[str, Any] = dc_field(default_factory=dict)
    assumptions: Mapping[str, Any] = dc_field(default_factory=dict)
    calculation_snapshot_id: Optional[str] = None
    emissions_log_id: Optional[str] = None
    factor_id: Optional[str] = None
    source_reference: Optional[str] = None
    scope3_category: Optional[int] = None
    actor_user_id: Optional[str] = None
    actor_organization_id: Optional[str] = None
    acting_for_organization_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        validate_estimation_method(self.estimation_method)
        assert_estimation_substantiated(
            estimation_method=self.estimation_method,
            inputs=self.inputs,
            assumptions=self.assumptions,
        )

    def as_row(self) -> dict[str, Any]:
        """Return the database payload for an ``estimation_records`` INSERT."""
        return {
            "organization_id": self.organization_id,
            "calculation_snapshot_id": self.calculation_snapshot_id,
            "emissions_log_id": self.emissions_log_id,
            "estimation_method": self.estimation_method,
            "inputs": dict(self.inputs),
            "assumptions": dict(self.assumptions),
            "factor_id": self.factor_id,
            "source_reference": self.source_reference,
            "scope3_category": self.scope3_category,
            "actor_user_id": self.actor_user_id,
            "actor_organization_id": self.actor_organization_id,
            "acting_for_organization_id": self.acting_for_organization_id,
        }


def assert_estimation_substantiated(
    *,
    estimation_method: Optional[str],
    inputs: Mapping[str, Any],
    assumptions: Mapping[str, Any],
) -> None:
    """Refuse an estimation record that substantiates nothing.

    A method alone is not substantive: "modelled" with no inputs and no
    assumptions describes nothing and could not be reviewed. At least one of
    ``inputs`` or ``assumptions`` must be non-empty.
    """
    validate_estimation_method(estimation_method)
    if not inputs and not assumptions:
        raise EstimationRecordRequiredError(
            "an estimation record must record at least one input or assumption; "
            "a method with no inputs and no assumptions does not substantiate the "
            "estimate and cannot be reviewed (T-INV-12)",
            details={"field": "inputs|assumptions"},
        )


def requires_estimation_record(
    *, data_quality: Optional[str], declared_estimated: bool = False
) -> bool:
    """True when this result must carry an estimation record.

    Either the data quality is an estimate classification, or the caller has
    explicitly declared the value estimated. The second clause matters because a
    manually-flagged estimate must not escape the rule by leaving data quality
    unclassified.
    """
    return declared_estimated or is_estimated(data_quality)
