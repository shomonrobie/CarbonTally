"""Phase 8 B1 — Disclosure Model foundation domain model (pure, no I/O).

Vocabulary, validators and ratifiable invariants for the B1 Disclosure Model
foundation (contract ``CARBONTALLY_PHASE8_B1_IMPLEMENTATION_CONTRACT_20260912.md``
§§9, 14–19, 25; PO decisions PQ-1…PQ-8). This module mirrors the style of
:mod:`domain.report_lifecycle`: it is dependency-free and performs **no I/O** —
the repository persists and the (future) API authorizes/audits.

Ratified semantic invariants encoded here:

* ``effective_class`` is the **authoritative** home of the derived
  requirement/applicability/capability outcome (PQ-3).
* ``value_status`` is a **narrow materialisation lifecycle only**
  (``PENDING`` | ``RESOLVED`` | ``UNRESOLVED``) and MUST NOT duplicate or
  reinterpret ``requirement_class`` / applicability / ``carbontally_capability``
  / ``effective_class`` (PQ-3).
* An unresolved requirement identifier may never carry an official identifier
  (D17 / DM-1).
* A not-in-force framework version carries no ``applicable_from`` (design §6.5).
* The report-instance binding is **authoritative** for the report period; where
  it references an applicability assessment, the two periods MUST agree (PQ-2).
* Approved/final report versions are immutable (D15; enforced at the
  application/service layer in B1 — PQ-4).
"""
from __future__ import annotations

from typing import Any, Optional

# ---------------------------------------------------------------------------
# Vocabularies (contract §9)
# ---------------------------------------------------------------------------
FRAMEWORK_CODES: tuple[str, ...] = ("GHG_PROTOCOL", "UK_SECR", "ESRS_E1")

FRAMEWORK_KINDS: tuple[str, ...] = (
    "accounting_foundation",
    "jurisdiction_statute",
    "eu_standard",
)

FRAMEWORK_VERSION_STATUSES: tuple[str, ...] = (
    "IN_FORCE",
    "ADOPTED_NOT_IN_FORCE",
    "SUPERSEDED",
    "WITHDRAWN",
)

REQUIREMENT_CLASSES: tuple[str, ...] = (
    "REQUIRED",
    "CONDITIONAL",
    "OPTIONAL",
    "NOT_APPLICABLE",
    "CUSTOMER_INPUT_REQUIRED",
    "UNDETERMINED",
    "NOT_SUPPORTED",
    "FUTURE",
)

#: CarbonTally capability — a property of the REQUIREMENT VERSION, distinct from
#: regulatory applicability and from value materialisation (D12).
CARBONTALLY_CAPABILITIES: tuple[str, ...] = (
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "STRUCTURED_INPUT_REQUIRED",
    "EXTERNAL_INPUT_REQUIRED",
    "MISSING_CAPABILITY",
    "FUTURE",
    "NOT_APPLICABLE_TO_PRODUCT",
)

SOURCE_KINDS: tuple[str, ...] = (
    "CALCULATION_AGGREGATE",
    "EMISSIONS_LOG_AGGREGATE",
    "FACTOR_PROVENANCE",
    "EVIDENCE_COMPLETENESS",
    "ENERGY_ACTIVITY",
    "INTENSITY_RATIO",
    "PRIOR_PERIOD_VALUE",
    "ORG_PROFILE_FACT",
    "CUSTOMER_INPUT",
)

AGGREGATIONS: tuple[str, ...] = ("SUM", "SUM_KG_CO2E", "DISTINCT_COUNT", "RATIO", "PASSTHROUGH")

IDENTIFIER_STATUSES: tuple[str, ...] = (
    "RESOLVED",
    "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION",
)
UNRESOLVED_IDENTIFIER = "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION"

REPORT_PURPOSE_CODES: tuple[str, ...] = (
    "ANNUAL_CARBON",
    "MANAGEMENT",
    "UK_SECR",
    "ESRS_E1_QUANT",
)

PURPOSE_VERSION_STATUSES: tuple[str, ...] = ("DRAFT", "ACTIVE", "SUPERSEDED")

# ---------------------------------------------------------------------------
# Audit actions (contract §24/§26) — reuse of the EXISTING audit taxonomy
# ---------------------------------------------------------------------------
#: ``head:verb`` action names for the B1 write paths that exist today. The
#: ``report`` head classifies every B1 catalogue/reporting write as a
#: ``CAT_REPORT`` entry under the existing taxonomy
#: (:func:`domain.audit.classify_action`) — B1 introduces **no** new audit table,
#: category or subsystem (contract §26).
AUDIT_FRAMEWORK_SEEDED = "report:disclosure_framework_seeded"
AUDIT_PURPOSE_SEEDED = "report:disclosure_purpose_seeded"
AUDIT_APPLICABILITY_ASSESSED = "report:disclosure_applicability_assessed"
AUDIT_REPORT_BOUND = "report:disclosure_report_bound"
AUDIT_VALUE_MATERIALISED = "report:disclosure_value_materialised"
AUDIT_EVIDENCE_LINKED = "report:disclosure_evidence_linked"

AUDIT_ACTIONS: tuple[str, ...] = (
    AUDIT_FRAMEWORK_SEEDED,
    AUDIT_PURPOSE_SEEDED,
    AUDIT_APPLICABILITY_ASSESSED,
    AUDIT_REPORT_BOUND,
    AUDIT_VALUE_MATERIALISED,
    AUDIT_EVIDENCE_LINKED,
)

#: Applicability states (D13/APPL). ``UNDETERMINED`` is first-class.
APPLICABILITY_STATUSES: tuple[str, ...] = (
    "APPLIES",
    "DOES_NOT_APPLY",
    "UNDETERMINED",
    "CUSTOMER_INPUT_REQUIRED",
)

CONSOLIDATION_APPROACHES: tuple[str, ...] = (
    "OPERATIONAL_CONTROL",
    "FINANCIAL_CONTROL",
    "EQUITY_SHARE",
)

#: PQ-3 — the ONLY materialisation lifecycle states. Deliberately NOT the
#: requirement/applicability/capability vocabulary.
VALUE_STATUSES: tuple[str, ...] = ("PENDING", "RESOLVED", "UNRESOLVED")

VALUE_KINDS: tuple[str, ...] = ("QUANTITATIVE", "QUALITATIVE", "NARRATIVE_BOUND", "SELECTION")

EVIDENCE_COMPLETENESS_STATES: tuple[str, ...] = ("COMPLETE", "PARTIAL", "UNAVAILABLE")

SCOPE2_METHODS: tuple[str, ...] = ("LOCATION_BASED", "MARKET_BASED")

#: Report-version states whose disclosure values must never be mutated (D15).
IMMUTABLE_REPORT_VERSION_STATUSES: tuple[str, ...] = ("APPROVED", "FINAL")

# ---------------------------------------------------------------------------
# Reference-seed identities (PQ-6 — identities ONLY; no regulatory content)
# ---------------------------------------------------------------------------
FRAMEWORK_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "code": "GHG_PROTOCOL",
        "name": "GHG Protocol Corporate Standard",
        "kind": "accounting_foundation",
        "is_primary_foundation": True,
    },
    {
        "code": "UK_SECR",
        "name": "UK Streamlined Energy and Carbon Reporting",
        "kind": "jurisdiction_statute",
        "is_primary_foundation": False,
    },
    {
        "code": "ESRS_E1",
        "name": "ESRS E1 Climate Change",
        "kind": "eu_standard",
        "is_primary_foundation": False,
    },
)

PURPOSE_SEEDS: tuple[dict[str, Any], ...] = (
    {"code": "ANNUAL_CARBON", "name": "Annual Carbon Report", "is_statutory_positioned": False},
    {"code": "MANAGEMENT", "name": "Management Report", "is_statutory_positioned": False},
    {"code": "UK_SECR", "name": "UK SECR Report", "is_statutory_positioned": True},
    {"code": "ESRS_E1_QUANT", "name": "ESRS E1 Quantitative Report", "is_statutory_positioned": True},
)


class DisclosureViolation(ValueError):
    """Raised when a B1 disclosure invariant would be violated."""


def _validate(value: object, allowed: tuple[str, ...], field: str) -> str:
    """Return ``value`` when it is one of ``allowed``, else raise."""
    if not isinstance(value, str) or value not in allowed:
        raise DisclosureViolation(
            f"invalid {field} {value!r}; expected one of {list(allowed)}"
        )
    return value


def validate_framework_code(value: str) -> str:
    return _validate(value, FRAMEWORK_CODES, "framework code")


def validate_framework_kind(value: str) -> str:
    return _validate(value, FRAMEWORK_KINDS, "framework kind")


def validate_framework_version_status(value: str) -> str:
    return _validate(value, FRAMEWORK_VERSION_STATUSES, "framework version status")


def validate_requirement_class(value: str) -> str:
    return _validate(value, REQUIREMENT_CLASSES, "requirement class")


def validate_carbontally_capability(value: str) -> str:
    return _validate(value, CARBONTALLY_CAPABILITIES, "carbontally capability")


def validate_source_kind(value: str) -> str:
    return _validate(value, SOURCE_KINDS, "source kind")


def validate_aggregation(value: str) -> str:
    return _validate(value, AGGREGATIONS, "aggregation")


def validate_identifier_status(value: str) -> str:
    return _validate(value, IDENTIFIER_STATUSES, "identifier status")


def validate_report_purpose_code(value: str) -> str:
    return _validate(value, REPORT_PURPOSE_CODES, "report purpose code")


def validate_purpose_version_status(value: str) -> str:
    return _validate(value, PURPOSE_VERSION_STATUSES, "purpose version status")


def validate_applicability_status(value: str) -> str:
    return _validate(value, APPLICABILITY_STATUSES, "applicability status")


def validate_consolidation_approach(value: str) -> str:
    return _validate(value, CONSOLIDATION_APPROACHES, "consolidation approach")


def validate_value_status(value: str) -> str:
    """Return ``value`` when it is a valid materialisation status."""
    return _validate(value, VALUE_STATUSES, "value status")


def validate_value_kind(value: str) -> str:
    return _validate(value, VALUE_KINDS, "value kind")


def validate_scope2_method(value: str) -> str:
    return _validate(value, SCOPE2_METHODS, "scope 2 method")


def validate_evidence_completeness(value: str) -> str:
    return _validate(value, EVIDENCE_COMPLETENESS_STATES, "evidence completeness")


# ---------------------------------------------------------------------------
# Ratified invariants (PQ-2 / PQ-3 / PQ-4 / D15 / D17 / DM-1)
# ---------------------------------------------------------------------------
def assert_value_status_is_materialisation_only(value_status: str) -> str:
    """PQ-3 — ``value_status`` must never carry classification semantics."""
    validate_value_status(value_status)
    if value_status in REQUIREMENT_CLASSES:  # pragma: no cover - unreachable given the set
        raise DisclosureViolation(
            f"value_status {value_status!r} must not carry requirement/applicability semantics"
        )
    return value_status


def assert_value_status_independent(value_status: str, effective_class: str) -> None:
    """PQ-3 — ``effective_class`` and ``value_status`` are separate dimensions."""
    assert_value_status_is_materialisation_only(value_status)
    validate_requirement_class(effective_class)
    if value_status in REQUIREMENT_CLASSES:  # pragma: no cover
        raise DisclosureViolation("value_status must not duplicate effective_class")


def assert_identifier_safety(
    identifier_status: str, official_identifier: Optional[str]
) -> None:
    """D17/DM-1 — an unresolved requirement may never carry an official id."""
    validate_identifier_status(identifier_status)
    if identifier_status != "RESOLVED" and official_identifier:
        raise DisclosureViolation(
            "an unresolved requirement identifier must not carry an official identifier"
        )


def assert_not_in_force_has_no_applicable_from(
    status: str, applicable_from: Optional[Any]
) -> None:
    """A not-in-force framework version carries no ``applicable_from`` (design §6.5)."""
    validate_framework_version_status(status)
    if status == "ADOPTED_NOT_IN_FORCE" and applicable_from is not None:
        raise DisclosureViolation(
            "an ADOPTED_NOT_IN_FORCE framework version must not carry applicable_from"
        )


def assert_period_order(period_start: Any, period_end: Any) -> None:
    """``reporting_period_end >= reporting_period_start``."""
    if period_start is None or period_end is None:
        raise DisclosureViolation("reporting period start and end are both required")
    if period_end < period_start:
        raise DisclosureViolation("reporting_period_end must be >= reporting_period_start")


def assert_periods_agree(
    *,
    binding_period_start: Any,
    binding_period_end: Any,
    assessment_period_start: Any,
    assessment_period_end: Any,
) -> None:
    """PQ-2 — a binding's period MUST equal a referenced assessment's period.

    The report-instance binding is authoritative for the report instance.
    """
    assert_period_order(binding_period_start, binding_period_end)
    assert_period_order(assessment_period_start, assessment_period_end)
    if (binding_period_start, binding_period_end) != (
        assessment_period_start,
        assessment_period_end,
    ):
        raise DisclosureViolation(
            "report-instance binding period must equal the referenced applicability "
            "assessment period (PQ-2 agreement invariant)"
        )


def is_immutable_report_version(status: str) -> bool:
    """D15/PQ-4 — approved/final report versions are immutable."""
    return status in IMMUTABLE_REPORT_VERSION_STATUSES


def assert_report_version_mutable(status: str) -> None:
    """Raise when a report version is approved/final (disclosure values frozen)."""
    if is_immutable_report_version(status):
        raise DisclosureViolation(
            f"report version status {status!r} is immutable; disclosure values cannot be mutated"
        )


def assert_same_organization(row_organization_id: Any, owner_organization_id: Any) -> None:
    """Cross-tenant invariant — a row belongs to exactly its owner's organisation."""
    if row_organization_id is None or owner_organization_id is None:
        raise DisclosureViolation("organization_id is required on organisation-scoped rows")
    if str(row_organization_id) != str(owner_organization_id):
        raise DisclosureViolation(
            "cross-tenant reference rejected: row organization_id must equal the owner organisation"
        )


