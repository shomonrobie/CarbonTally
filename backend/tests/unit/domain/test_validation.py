"""Unit tests for domain.validation (Phase 9A domain contracts)."""
from __future__ import annotations

import pytest

from dataclasses import FrozenInstanceError
from domain.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSeverity,
)


def make_issue(
    code: str = "VAL_X",
    severity: ValidationSeverity = ValidationSeverity.ERROR,
    entity_id: str = "e-1",
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=severity,
        message="some message",
        entity_type="emissions_log",
        entity_id=entity_id,
    )


class TestValidationSeverity:
    def test_values(self) -> None:
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.SUGGESTION.value == "suggestion"


class TestValidationIssue:
    def test_constructs(self) -> None:
        issue = make_issue()
        assert issue.code == "VAL_X"
        assert issue.severity is ValidationSeverity.ERROR
        assert issue.entity_type == "emissions_log"
        assert issue.context == {}

    def test_error_is_blocking(self) -> None:
        assert make_issue().is_blocking is True

    def test_warning_is_not_blocking(self) -> None:
        issue = make_issue(severity=ValidationSeverity.WARNING)
        assert issue.is_blocking is False

    def test_is_immutable(self) -> None:
        with pytest.raises(FrozenInstanceError):
            make_issue().code = "changed"  # type: ignore[misc]

    def test_rejects_empty_code(self) -> None:
        with pytest.raises(ValueError, match="code"):
            make_issue(code="")

    def test_rejects_empty_message(self) -> None:
        with pytest.raises(ValueError, match="message"):
            ValidationIssue(
                code="VAL_X",
                severity=ValidationSeverity.ERROR,
                message="",
                entity_type="emissions_log",
                entity_id="e-1",
            )

    def test_rejects_empty_entity_type(self) -> None:
        with pytest.raises(ValueError, match="entity_type"):
            ValidationIssue(
                code="VAL_X",
                severity=ValidationSeverity.ERROR,
                message="msg",
                entity_type="",
                entity_id="e-1",
            )

    def test_rejects_empty_entity_id(self) -> None:
        with pytest.raises(ValueError, match="entity_id"):
            make_issue(entity_id="")


class TestValidationReport:
    def test_empty_report_is_ok(self) -> None:
        assert ValidationReport().ok is True
        assert ValidationReport().counts == {
            "error": 0,
            "warning": 0,
            "suggestion": 0,
        }
        assert ValidationReport().blocking_errors == ()

    def test_ok_false_with_error(self) -> None:
        report = ValidationReport(issues=(make_issue(),))
        assert report.ok is False

    def test_ok_true_with_warnings_only(self) -> None:
        report = ValidationReport(
            issues=(make_issue(severity=ValidationSeverity.WARNING),)
        )
        assert report.ok is True

    def test_counts_by_severity(self) -> None:
        report = ValidationReport(
            issues=(
                make_issue(code="a"),
                make_issue(code="b"),
                make_issue(code="c", severity=ValidationSeverity.WARNING),
            )
        )
        assert report.counts == {"error": 2, "warning": 1, "suggestion": 0}

    def test_blocking_errors(self) -> None:
        report = ValidationReport(
            issues=(
                make_issue(code="a"),
                make_issue(code="b", severity=ValidationSeverity.WARNING),
            )
        )
        blocking = report.blocking_errors
        assert len(blocking) == 1
        assert blocking[0].code == "a"

    def test_merge_combines_issues(self) -> None:
        left = ValidationReport(issues=(make_issue(code="a"),))
        right = ValidationReport(issues=(make_issue(code="b"),))
        merged = left.merge(right)
        assert [i.code for i in merged.issues] == ["a", "b"]

    def test_merge_is_immutable(self) -> None:
        left = ValidationReport(issues=(make_issue(code="a"),))
        right = ValidationReport(issues=(make_issue(code="b"),))
        merged = left.merge(right)
        assert len(left.issues) == 1
        assert len(right.issues) == 1
        assert len(merged.issues) == 2


class TestValidationRequest:
    def test_constructs(self) -> None:
        request = ValidationRequest(organization_id="org-1", reporting_year=2025)
        assert request.organization_id == "org-1"
        assert request.reporting_year == 2025
        assert request.period is None
        assert request.scope_filter is None
        assert request.entity_ids == ()
        assert request.strict is False

    def test_rejects_empty_organization(self) -> None:
        with pytest.raises(ValueError, match="organization_id"):
            ValidationRequest(organization_id="", reporting_year=2025)

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError, match="reporting_year"):
            ValidationRequest(organization_id="org-1", reporting_year=1899)
