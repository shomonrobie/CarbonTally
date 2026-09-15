"""Phase 8 B3 — Disclosure projection domain model (pure, no I/O).

Producer registry, deterministic aggregation, projection decisions, 
``effective_class`` derivation and intensity-ratio arithmetic for Batch B3
(contract ``CARBONTALLY_PHASE8_B3_IMPLEMENTATION_CONTRACT_20260913.md`` §§7, 9–11).

Governance encoded here:

* The ``source_kind`` producer set is **closed** (design: no DSL). The registry
  covers exactly :data:`domain.disclosure.SOURCE_KINDS`; an unknown kind raises.
* ``value_status`` is the **narrow materialisation lifecycle only**
  (``PENDING``/``RESOLVED``/``UNRESOLVED``, PQ-3) — never the requirement,
  applicability or capability vocabulary.
* ``NOT_SUPPORTED`` (CarbonTally cannot produce it) and
  ``CUSTOMER_INPUT_REQUIRED`` (the customer must supply it) are **never
  conflated** (``DM-5``; Decision Record §8): they produce different reasons.
* ``UNDETERMINED`` applicability can never be coerced to a value or to
  not-applicable (``APPL`` / D13).
* No legal determination is asserted anywhere in this module.
* No calculation is performed: aggregation reads already-authoritative rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

from core.units import normalize_unit
from domain.disclosure import (
    AGGREGATIONS,
    APPLICABILITY_STATUSES,
    SOURCE_KINDS,
    VALUE_STATUSES,
    DisclosureViolation,
    validate_aggregation,
    validate_source_kind,
)

# ---------------------------------------------------------------------------
# Producer registry (closed set — contract §7.1)
# ---------------------------------------------------------------------------
#: Every ratified ``source_kind`` maps to its permitted aggregations and rules.
PRODUCER_REGISTRY: Mapping[str, Mapping[str, Any]] = {
    "CALCULATION_AGGREGATE": {
        "aggregations": ("SUM_KG_CO2E", "SUM", "DISTINCT_COUNT", "PASSTHROUGH"),
        "default_aggregation": "SUM_KG_CO2E",
        "reads": "persisted calculation_snapshots",
    },
    "EMISSIONS_LOG_AGGREGATE": {
        "aggregations": ("SUM_KG_CO2E", "SUM", "DISTINCT_COUNT"),
        "default_aggregation": "SUM_KG_CO2E",
        "reads": "persisted emissions_logs",
    },
    "FACTOR_PROVENANCE": {
        "aggregations": ("PASSTHROUGH", "DISTINCT_COUNT"),
        "default_aggregation": "PASSTHROUGH",
        "reads": "snapshot factor_kind/factor_id/customer_factor_id",
    },
    "EVIDENCE_COMPLETENESS": {
        "aggregations": ("RATIO", "DISTINCT_COUNT"),
        "default_aggregation": "RATIO",
        "reads": "disclosure_value_evidence + B2 line links",
    },
    "ENERGY_ACTIVITY": {
        "aggregations": ("SUM", "DISTINCT_COUNT"),
        "default_aggregation": "SUM",
        "reads": "snapshot activity quantity/unit",
    },
    "INTENSITY_RATIO": {
        "aggregations": ("PASSTHROUGH",),
        "default_aggregation": "PASSTHROUGH",
        "reads": "persisted disclosure_intensity_ratios",
    },
    "PRIOR_PERIOD_VALUE": {
        "aggregations": ("PASSTHROUGH",),
        "default_aggregation": "PASSTHROUGH",
        "reads": "prior disclosure_values row",
    },
    "ORG_PROFILE_FACT": {
        "aggregations": ("PASSTHROUGH",),
        "default_aggregation": "PASSTHROUGH",
        "reads": "organisation profile / facility facts",
    },
    "CUSTOMER_INPUT": {
        "aggregations": ("PASSTHROUGH",),
        "default_aggregation": "PASSTHROUGH",
        "reads": "customer-supplied input",
    },
}

#: Capabilities that mean CarbonTally cannot produce the value at all.
UNSUPPORTED_CAPABILITIES: tuple[str, ...] = (
    "MISSING_CAPABILITY",
    "NOT_APPLICABLE_TO_PRODUCT",
    "FUTURE",
)

#: Requirement classes that mean the requirement is not producible now.
UNSUPPORTED_REQUIREMENT_CLASSES: tuple[str, ...] = ("NOT_SUPPORTED", "FUTURE")


def assert_producer_registry_complete() -> None:
    """Fail loudly if the registry diverges from the ratified ``SOURCE_KINDS``."""
    missing = [k for k in SOURCE_KINDS if k not in PRODUCER_REGISTRY]
    extra = [k for k in PRODUCER_REGISTRY if k not in SOURCE_KINDS]
    if missing or extra:
        raise DisclosureViolation(
            f"B3 producer registry drift: missing={missing} extra={extra}"
        )
    for kind, entry in PRODUCER_REGISTRY.items():
        for aggregation in entry["aggregations"]:
            validate_aggregation(aggregation)
        if entry["default_aggregation"] not in entry["aggregations"]:
            raise DisclosureViolation(
                f"B3 producer registry: default aggregation for {kind} is not permitted"
            )


def registry_entry(source_kind: str) -> Mapping[str, Any]:
    """Return the registry entry for a ratified ``source_kind`` (fail loudly)."""
    kind = validate_source_kind(source_kind)
    try:
        return PRODUCER_REGISTRY[kind]
    except KeyError:  # pragma: no cover - guarded by assert_producer_registry_complete
        raise DisclosureViolation(f"B3: no producer registered for {kind}") from None


def permitted_aggregations(source_kind: str) -> tuple[str, ...]:
    return tuple(registry_entry(source_kind)["aggregations"])


# ---------------------------------------------------------------------------
# Deterministic aggregation (contract §7.2/§7.3)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AggregateResult:
    """Outcome of aggregating authoritative rows. ``None`` means 'no value'."""

    numeric_value: Optional[Decimal]
    value_unit: Optional[str]
    row_count: int
    reason: Optional[str] = None

    @property
    def materialised(self) -> bool:
        return self.numeric_value is not None or self.value_unit is not None


def _to_decimal(value: Any, field: str) -> Decimal:
    if value is None:
        raise DisclosureViolation(f"B3 aggregation: row is missing {field}")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise DisclosureViolation(f"B3 aggregation: {field} is not numeric: {value!r}") from exc


def aggregate(aggregation: str, rows: Sequence[Mapping[str, Any]]) -> AggregateResult:
    """Aggregate already-authoritative rows. Never recomputes an emission."""
    agg = validate_aggregation(aggregation)
    count = len(rows)
    if count == 0:
        return AggregateResult(None, None, 0, reason="no authoritative rows for the period")

    if agg == "SUM_KG_CO2E":
        total = sum((_to_decimal(r.get("co2e_kg"), "co2e_kg") for r in rows), Decimal("0"))
        return AggregateResult(total, "kgCO2e", count)

    if agg == "SUM":
        units: list[str] = []
        for row in rows:
            unit = row.get("unit")
            if unit:
                units.append(normalize_unit(str(unit)) or str(unit))
        distinct = sorted(set(units))
        if len(distinct) > 1:
            raise DisclosureViolation(
                f"B3 aggregation: SUM requires one normalised unit, found {distinct}"
            )
        total = sum((_to_decimal(r.get("quantity"), "quantity") for r in rows), Decimal("0"))
        return AggregateResult(total, distinct[0] if distinct else None, count)

    if agg == "DISTINCT_COUNT":
        keys = set()
        for row in rows:
            key = row.get("natural_key")
            if key is None:
                raise DisclosureViolation("B3 aggregation: DISTINCT_COUNT requires natural_key")
            keys.add(key)
        return AggregateResult(Decimal(len(keys)), "count", count)

    if agg == "RATIO":
        numerator = sum((_to_decimal(r.get("numerator"), "numerator") for r in rows), Decimal("0"))
        denominator = sum((_to_decimal(r.get("denominator"), "denominator") for r in rows), Decimal("0"))
        ratio = compute_intensity_ratio(numerator, denominator)
        if ratio is None:
            return AggregateResult(None, None, count, reason="ratio denominator is zero")
        return AggregateResult(ratio, None, count)

    if agg == "PASSTHROUGH":
        if count != 1:
            raise DisclosureViolation(
                f"B3 aggregation: PASSTHROUGH expects exactly one row, got {count}"
            )
        row = rows[0]
        value = row.get("value", row.get("quantity", row.get("co2e_kg")))
        if value is None:
            return AggregateResult(None, None, count, reason="authoritative row carries no value")
        return AggregateResult(_to_decimal(value, "value"), row.get("unit"), count)

    raise DisclosureViolation(f"B3 aggregation: unsupported aggregation {agg!r}")


def compute_intensity_ratio(numerator: Any, denominator: Any) -> Optional[Decimal]:
    """Deterministic intensity ratio. A zero/absent denominator yields no value."""
    if numerator is None or denominator is None:
        return None
    num = _to_decimal(numerator, "numerator")
    den = _to_decimal(denominator, "denominator")
    if den == 0:
        return None
    if den < 0:
        raise DisclosureViolation("B3 intensity: denominator must be positive")
    return (num / den).normalize()


# ---------------------------------------------------------------------------
# Projection decision (contract §7.2, §11) — deterministic precedence
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProjectionDecision:
    """The outcome of planning one disclosure requirement for one report version."""

    value_status: str
    effective_class: str
    numeric_value: Optional[Decimal]
    value_unit: Optional[str]
    reason: Optional[str]
    source_kind: Optional[str]

    @property
    def materialised(self) -> bool:
        return self.value_status == "RESOLVED"


def derive_effective_class(
    *,
    requirement_class: str,
    applicability_status: str,
    carbontally_capability: str,
) -> str:
    """Derive the authoritative ``effective_class`` (PQ-3 home of the outcome).

    Precedence (documented and test-locked): applicability -> capability ->
    requirement class. ``UNDETERMINED`` is never coerced to not-applicable.
    """
    if applicability_status not in APPLICABILITY_STATUSES:
        raise DisclosureViolation(f"B3: unknown applicability status {applicability_status!r}")
    if applicability_status == "DOES_NOT_APPLY":
        return "NOT_APPLICABLE"
    if applicability_status == "UNDETERMINED":
        return "UNDETERMINED"
    if applicability_status == "CUSTOMER_INPUT_REQUIRED":
        return "CUSTOMER_INPUT_REQUIRED"
    if carbontally_capability in UNSUPPORTED_CAPABILITIES:
        return "FUTURE" if carbontally_capability == "FUTURE" else "NOT_SUPPORTED"
    if requirement_class in UNSUPPORTED_REQUIREMENT_CLASSES:
        return requirement_class
    return requirement_class


def _reason_for_effective_class(effective_class: str) -> str:
    """Distinct, non-conflatable reasons (DM-5; Decision Record §8)."""
    return {
        "NOT_APPLICABLE": "not applicable for this reporting period and organisation",
        "UNDETERMINED": "applicability undetermined - insufficient information",
        "CUSTOMER_INPUT_REQUIRED": "customer input required",
        "NOT_SUPPORTED": "not supported by CarbonTally",
        "FUTURE": "scheduled for a future CarbonTally capability",
    }[effective_class]


def decide_projection(
    *,
    requirement_class: str,
    carbontally_capability: str,
    applicability_status: str,
    source_kind: Optional[str] = None,
    aggregation: Optional[str] = None,
    rows: Sequence[Mapping[str, Any]] = (),
    customer_input: Any = None,
) -> ProjectionDecision:
    """Plan one requirement's disclosure value without writing anything."""
    effective = derive_effective_class(
        requirement_class=requirement_class,
        applicability_status=applicability_status,
        carbontally_capability=carbontally_capability,
    )

    if effective in ("NOT_APPLICABLE", "UNDETERMINED", "NOT_SUPPORTED", "FUTURE"):
        return ProjectionDecision(
            value_status="UNRESOLVED",
            effective_class=effective,
            numeric_value=None,
            value_unit=None,
            reason=_reason_for_effective_class(effective),
            source_kind=None,
        )

    if effective == "CUSTOMER_INPUT_REQUIRED":
        if customer_input is None:
            return ProjectionDecision(
                value_status="UNRESOLVED",
                effective_class=effective,
                numeric_value=None,
                value_unit=None,
                reason=_reason_for_effective_class(effective),
                source_kind="CUSTOMER_INPUT",
            )
        value = customer_input.get("value") if isinstance(customer_input, Mapping) else customer_input
        unit = customer_input.get("unit") if isinstance(customer_input, Mapping) else None
        numeric: Optional[Decimal]
        try:
            numeric = _to_decimal(value, "customer_input")
        except DisclosureViolation:
            numeric = None
        return ProjectionDecision(
            value_status="RESOLVED",
            effective_class=effective,
            numeric_value=numeric,
            value_unit=unit,
            reason=None,
            source_kind="CUSTOMER_INPUT",
        )

    if source_kind is None:
        raise DisclosureViolation("B3: a source_kind is required to materialise a value")
    kind = validate_source_kind(source_kind)
    permitted = permitted_aggregations(kind)
    agg = aggregation or str(registry_entry(kind)["default_aggregation"])
    if agg not in permitted:
        raise DisclosureViolation(
            f"B3: aggregation {agg!r} is not permitted for {kind} (permitted={list(permitted)})"
        )

    result = aggregate(agg, rows)
    if not result.materialised:
        return ProjectionDecision(
            value_status="UNRESOLVED",
            effective_class=effective,
            numeric_value=None,
            value_unit=None,
            reason=result.reason or "no value could be derived",
            source_kind=kind,
        )
    return ProjectionDecision(
        value_status="RESOLVED",
        effective_class=effective,
        numeric_value=result.numeric_value,
        value_unit=result.value_unit,
        reason=None,
        source_kind=kind,
    )


# ---------------------------------------------------------------------------
# Applicability guards (APPL / D13) — never a legal determination
# ---------------------------------------------------------------------------
#: Phrases that would assert a legal conclusion. CarbonTally records an
#: assessment with a basis; it does not give legal advice (APPL boundary §15).
FORBIDDEN_LEGAL_CLAIMS: tuple[str, ...] = (
    "legal advice",
    "legally required",
    "legally binding",
    "compliant with the law",
    "we certify",
    "we confirm compliance",
)


def assert_no_legal_determination(text: Optional[str]) -> None:
    """Raise if a basis/description asserts a legal determination (APPL)."""
    if not text:
        return
    lowered = text.lower()
    for phrase in FORBIDDEN_LEGAL_CLAIMS:
        if phrase in lowered:
            raise DisclosureViolation(
                f"B3 applicability: basis must not assert a legal determination ({phrase!r})"
            )


def validate_applicability_basis(basis: Optional[str], assessed_status: str) -> str:
    """A recorded applicability assessment always needs a real, non-legal basis."""
    if assessed_status not in APPLICABILITY_STATUSES:
        raise DisclosureViolation(f"B3 applicability: unknown status {assessed_status!r}")
    if basis is None or not basis.strip():
        raise DisclosureViolation("B3 applicability: basis is required")
    assert_no_legal_determination(basis)
    return basis.strip()


assert_producer_registry_complete()


def unmapped_decision(
    *,
    requirement_class: str,
    carbontally_capability: str,
    applicability_status: str,
) -> ProjectionDecision:
    """Decision for a requirement with **no producer mapping recorded**.

    B3 authors no mapping content (``B3-D8``; ``PQ-6``): when the ratified
    mapping table carries no row, the honest outcome is an ``UNRESOLVED`` value
    with an explicit reason — never a guessed producer and never a zero. Class
    level blocks (applicability/capability/requirement class) still take
    precedence, so their ratified reasons are preserved.
    """
    effective = derive_effective_class(
        requirement_class=requirement_class,
        applicability_status=applicability_status,
        carbontally_capability=carbontally_capability,
    )
    if effective in (
        "NOT_APPLICABLE",
        "UNDETERMINED",
        "NOT_SUPPORTED",
        "FUTURE",
        # A customer-input requirement cannot be produced by any mapping: the
        # customer must supply the value (DM-5: distinct, never conflated).
        "CUSTOMER_INPUT_REQUIRED",
    ):
        return ProjectionDecision(
            value_status="UNRESOLVED",
            effective_class=effective,
            numeric_value=None,
            value_unit=None,
            reason=_reason_for_effective_class(effective),
            source_kind=None,
        )
    return ProjectionDecision(
        value_status="UNRESOLVED",
        effective_class=effective,
        numeric_value=None,
        value_unit=None,
        reason="no producer mapping recorded for this requirement",
        source_kind=None,
    )
