"""Phase 8 B1 — Disclosure Model domain tests (implementation tests).

Pure, no DB. Covers the ratified invariants PQ-2 / PQ-3 / PQ-4 plus the schema
vocabularies (contract §9, §17, §27.B).
"""
from __future__ import annotations

import datetime

import pytest

from domain.disclosure import (
    APPLICABILITY_STATUSES,
    CONSOLIDATION_APPROACHES,
    FRAMEWORK_CODES,
    FRAMEWORK_KINDS,
    FRAMEWORK_SEEDS,
    FRAMEWORK_VERSION_STATUSES,
    DisclosureViolation,
    PURPOSE_SEEDS,
    REPORT_PURPOSE_CODES,
    VALUE_STATUSES,
    assert_identifier_safety,
    assert_not_in_force_has_no_applicable_from,
    assert_period_order,
    assert_periods_agree,
    assert_report_version_mutable,
    assert_same_organization,
    assert_value_status_independent,
    assert_value_status_is_materialisation_only,
    is_immutable_report_version,
    validate_applicability_status,
    validate_consolidation_approach,
    validate_framework_code,
    validate_framework_kind,
    validate_report_purpose_code,
    validate_requirement_class,
    validate_value_status,
)

D = datetime.date


# --- Vocabularies (contract §9) --------------------------------------------
def test_framework_vocabulary_matches_contract() -> None:
    assert FRAMEWORK_CODES == ("GHG_PROTOCOL", "UK_SECR", "ESRS_E1")
    assert FRAMEWORK_KINDS == ("accounting_foundation", "jurisdiction_statute", "eu_standard")
    assert FRAMEWORK_VERSION_STATUSES == (
        "IN_FORCE",
        "ADOPTED_NOT_IN_FORCE",
        "SUPERSEDED",
        "WITHDRAWN",
    )


def test_purpose_and_applicability_vocabulary() -> None:
    assert REPORT_PURPOSE_CODES == ("ANNUAL_CARBON", "MANAGEMENT", "UK_SECR", "ESRS_E1_QUANT")
    assert APPLICABILITY_STATUSES == (
        "APPLIES",
        "DOES_NOT_APPLY",
        "UNDETERMINED",
        "CUSTOMER_INPUT_REQUIRED",
    )
    assert CONSOLIDATION_APPROACHES == (
        "OPERATIONAL_CONTROL",
        "FINANCIAL_CONTROL",
        "EQUITY_SHARE",
    )


def test_reference_seeds_are_identity_only() -> None:
    assert {s["code"] for s in FRAMEWORK_SEEDS} == {"GHG_PROTOCOL", "UK_SECR", "ESRS_E1"}
    assert {s["code"] for s in PURPOSE_SEEDS} == {
        "ANNUAL_CARBON",
        "MANAGEMENT",
        "UK_SECR",
        "ESRS_E1_QUANT",
    }
    # Identity-only: no regulatory content (versions/thresholds) is seeded here.
    for seed in FRAMEWORK_SEEDS:
        assert "version_label" not in seed
        assert "applicable_from" not in seed


def test_validators_accept_valid_and_reject_invalid() -> None:
    assert validate_framework_code("UK_SECR") == "UK_SECR"
    assert validate_framework_kind("eu_standard") == "eu_standard"
    assert validate_report_purpose_code("MANAGEMENT") == "MANAGEMENT"
    assert validate_applicability_status("UNDETERMINED") == "UNDETERMINED"
    assert validate_consolidation_approach("EQUITY_SHARE") == "EQUITY_SHARE"
    assert validate_requirement_class("NOT_SUPPORTED") == "NOT_SUPPORTED"
    with pytest.raises(DisclosureViolation):
        validate_framework_code("GRI")
    with pytest.raises(DisclosureViolation):
        validate_applicability_status("MAYBE")


# --- PQ-3: value_status is materialisation-only ----------------------------
def test_value_status_allows_only_the_three_materialisation_states() -> None:
    assert VALUE_STATUSES == ("PENDING", "RESOLVED", "UNRESOLVED")
    for good in VALUE_STATUSES:
        assert validate_value_status(good) == good
        assert assert_value_status_is_materialisation_only(good) == good


@pytest.mark.parametrize(
    "bad",
    ["CUSTOMER_INPUT_REQUIRED", "NOT_SUPPORTED", "NOT_APPLICABLE", "UNDETERMINED"],
)
def test_value_status_rejects_requirement_classification_values(bad: str) -> None:
    """The four values the earlier contract proposal wrongly allowed are rejected."""
    with pytest.raises(DisclosureViolation):
        validate_value_status(bad)
    with pytest.raises(DisclosureViolation):
        assert_value_status_is_materialisation_only(bad)


def test_effective_class_and_value_status_are_independent() -> None:
    assert_value_status_independent("PENDING", "CUSTOMER_INPUT_REQUIRED")
    assert_value_status_independent("UNRESOLVED", "NOT_SUPPORTED")
    with pytest.raises(DisclosureViolation):
        assert_value_status_independent("CUSTOMER_INPUT_REQUIRED", "REQUIRED")
    with pytest.raises(DisclosureViolation):
        assert_value_status_independent("PENDING", "BOGUS_CLASS")


# --- D17/DM-1: identifier safety -------------------------------------------
def test_identifier_safety_blocks_invented_official_identifiers() -> None:
    assert_identifier_safety("UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION", None)
    assert_identifier_safety("RESOLVED", "E1-6")
    with pytest.raises(DisclosureViolation):
        assert_identifier_safety("UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION", "E1-6")


# --- design §6.5: not-in-force version has no applicable_from --------------
def test_not_in_force_version_carries_no_applicable_from() -> None:
    assert_not_in_force_has_no_applicable_from("ADOPTED_NOT_IN_FORCE", None)
    assert_not_in_force_has_no_applicable_from("IN_FORCE", D(2024, 1, 1))
    with pytest.raises(DisclosureViolation):
        assert_not_in_force_has_no_applicable_from("ADOPTED_NOT_IN_FORCE", D(2024, 1, 1))


# --- DM-3 / PQ-2: period order + agreement invariant -----------------------
def test_period_order_is_enforced() -> None:
    assert_period_order(D(2025, 1, 1), D(2025, 12, 31))
    assert_period_order(D(2025, 4, 6), D(2025, 4, 6))  # equal is allowed
    with pytest.raises(DisclosureViolation):
        assert_period_order(D(2025, 12, 31), D(2025, 1, 1))


def test_pq2_period_agreement_invariant() -> None:
    assert_periods_agree(
        binding_period_start=D(2025, 1, 1),
        binding_period_end=D(2025, 12, 31),
        assessment_period_start=D(2025, 1, 1),
        assessment_period_end=D(2025, 12, 31),
    )
    with pytest.raises(DisclosureViolation):
        assert_periods_agree(
            binding_period_start=D(2025, 1, 1),
            binding_period_end=D(2025, 12, 31),
            assessment_period_start=D(2025, 1, 1),
            assessment_period_end=D(2025, 6, 30),
        )


def test_non_calendar_period_is_representable() -> None:
    assert_period_order(D(2025, 4, 6), D(2026, 4, 5))


# --- PQ-4 / D15: immutability ----------------------------------------------
def test_report_version_immutability() -> None:
    assert is_immutable_report_version("APPROVED")
    assert is_immutable_report_version("FINAL")
    assert not is_immutable_report_version("DRAFT")
    for mutable in ("DRAFT", "REVIEWED", "CHANGES_REQUESTED", "REJECTED"):
        assert_report_version_mutable(mutable)
    for frozen in ("APPROVED", "FINAL"):
        with pytest.raises(DisclosureViolation):
            assert_report_version_mutable(frozen)


# --- Cross-tenant invariant -------------------------------------------------
def test_cross_tenant_reference_is_rejected() -> None:
    assert_same_organization("org-a", "org-a")
    with pytest.raises(DisclosureViolation):
        assert_same_organization("org-a", "org-b")
    with pytest.raises(DisclosureViolation):
        assert_same_organization(None, "org-a")

