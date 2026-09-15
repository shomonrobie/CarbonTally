"""Unit tests for the B4 narrative/finalisation domain model (pure, no I/O)."""
from __future__ import annotations

import pytest

from domain.disclosure import DisclosureViolation
from domain.disclosure_narrative import (
    NARRATIVE_KINDS,
    FinalisationAssessment,
    FinalisationItem,
    assert_author_role,
    assert_can_author,
    assert_narrative_binding,
    assert_states_are_not_collapsed,
    evaluate_finalisation,
    validate_narrative_body,
    validate_narrative_kind,
)


# --- body / plain text / A3 -------------------------------------------------
def test_body_is_stripped_and_returned() -> None:
    assert validate_narrative_body("  Our methodology changed.  ") == "Our methodology changed."


def test_empty_body_is_rejected() -> None:
    for body in (None, "", "   ", "\n\t "):
        with pytest.raises(DisclosureViolation):
            validate_narrative_body(body)


def test_markup_is_rejected() -> None:
    for body in ("<b>bold</b>", "<script>alert(1)</script>", "javascript:alert(1)"):
        with pytest.raises(DisclosureViolation):
            validate_narrative_body(body)


def test_no_arbitrary_length_limit_exists() -> None:
    """A3: no invented character cap - a long, real narrative is accepted."""
    long_body = "x" * 20000
    assert validate_narrative_body(long_body) == long_body


# --- binding / roles / immutability -----------------------------------------
def test_narrative_requires_a_requirement_binding() -> None:
    with pytest.raises(DisclosureViolation):
        assert_narrative_binding(None)
    assert assert_narrative_binding("rv-1") == "rv-1"


def test_only_owner_or_admin_may_author() -> None:
    for role in ("owner", "org_owner", "admin", "org_admin"):
        assert_author_role(role)
    for role in ("member", "viewer", "user", "consultant", "pe_staff", "staff", None):
        with pytest.raises(DisclosureViolation):
            assert_author_role(role)


def test_authoring_refused_on_immutable_versions() -> None:
    assert_can_author("DRAFT")
    assert_can_author("REVIEWED")
    for status in ("APPROVED", "FINAL"):
        with pytest.raises(DisclosureViolation):
            assert_can_author(status)


def test_narrative_kind_vocabulary_is_closed() -> None:
    for kind in NARRATIVE_KINDS:
        assert validate_narrative_kind(kind) == kind
    with pytest.raises(DisclosureViolation):
        validate_narrative_kind("FREE_FORM")


# --- DM-5 finalisation gate -------------------------------------------------
def test_all_resolved_can_finalise() -> None:
    assessment = evaluate_finalisation(
        [
            {"requirement_version_id": "a", "effective_class": "REQUIRED", "value_status": "RESOLVED"},
            {"requirement_version_id": "b", "effective_class": "NOT_SUPPORTED", "value_status": "RESOLVED"},
        ]
    )
    assert assessment.can_finalise is True
    assert assessment.blocking == []


def test_unresolved_required_blocks() -> None:
    assessment = evaluate_finalisation(
        [{"requirement_version_id": "a", "effective_class": "REQUIRED", "value_status": "UNRESOLVED", "reason": "no rows"}]
    )
    assert assessment.can_finalise is False
    assert [i.requirement_version_id for i in assessment.blocked_by_unresolved_required] == ["a"]


def test_customer_input_required_blocks_with_its_own_reason() -> None:
    assessment = evaluate_finalisation(
        [{"requirement_version_id": "a", "effective_class": "CUSTOMER_INPUT_REQUIRED", "value_status": "UNRESOLVED", "reason": "customer input required"}]
    )
    assert assessment.can_finalise is False
    assert [i.requirement_version_id for i in assessment.blocked_by_customer_input] == ["a"]
    assert assessment.surfaced == []


def test_not_supported_is_surfaced_not_blocking_and_never_satisfied() -> None:
    assessment = evaluate_finalisation(
        [{"requirement_version_id": "a", "effective_class": "NOT_SUPPORTED", "value_status": "UNRESOLVED", "reason": "not supported by CarbonTally"}]
    )
    assert assessment.can_finalise is True, "NOT_SUPPORTED surfaces; it does not block (DM-5)"
    assert [i.requirement_version_id for i in assessment.surfaced] == ["a"]
    assert assessment.informational == [], "a NOT_SUPPORTED item is never presented as satisfied"
    assert assessment.blocking == []


def test_the_two_states_are_never_collapsed() -> None:
    assessment = evaluate_finalisation(
        [
            {"requirement_version_id": "needs-input", "effective_class": "CUSTOMER_INPUT_REQUIRED", "value_status": "UNRESOLVED"},
            {"requirement_version_id": "unsupported", "effective_class": "NOT_SUPPORTED", "value_status": "UNRESOLVED"},
        ]
    )
    assert assessment.can_finalise is False
    assert {i.requirement_version_id for i in assessment.blocking} == {"needs-input"}
    assert {i.requirement_version_id for i in assessment.surfaced} == {"unsupported"}
    assert_states_are_not_collapsed(assessment)
    # A forged collapse is detected.
    forged = FinalisationAssessment(
        can_finalise=False,
        blocking=[FinalisationItem("x", "CUSTOMER_INPUT_REQUIRED", "UNRESOLVED")],
        surfaced=[FinalisationItem("x", "NOT_SUPPORTED", "UNRESOLVED")],
    )
    with pytest.raises(DisclosureViolation):
        assert_states_are_not_collapsed(forged)


def test_not_applicable_and_undetermined_do_not_block() -> None:
    assessment = evaluate_finalisation(
        [
            {"requirement_version_id": "a", "effective_class": "NOT_APPLICABLE", "value_status": "UNRESOLVED"},
            {"requirement_version_id": "b", "effective_class": "UNDETERMINED", "value_status": "UNRESOLVED"},
        ]
    )
    assert assessment.can_finalise is True
    assert len(assessment.informational) == 2
