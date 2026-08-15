"""Unit tests for the Issue domain (V3 ADR-V3-009)."""

from __future__ import annotations

import pytest

from domain.issue import (
    ISSUE_SEVERITIES,
    ISSUE_STATUSES,
    ISSUE_TYPES,
    Issue,
    _ISSUE_TRANSITIONS,
)


def make_issue(**overrides) -> Issue:
    defaults = dict(id="issue-1", title="Missing invoice page")
    defaults.update(overrides)
    return Issue(**defaults)


class TestIssue:
    def test_valid_issue(self) -> None:
        issue = make_issue()
        assert issue.status == "open"
        assert issue.issue_type == "exception"
        assert issue.severity == "medium"

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(ValueError):
            make_issue(title="")

    def test_rejects_bad_type_severity_status(self) -> None:
        with pytest.raises(ValueError):
            make_issue(issue_type="bogus")
        with pytest.raises(ValueError):
            make_issue(severity="bogus")
        with pytest.raises(ValueError):
            make_issue(status="bogus")

    def test_rejects_negative_priority_and_escalation(self) -> None:
        with pytest.raises(ValueError):
            make_issue(priority=-1)
        with pytest.raises(ValueError):
            make_issue(escalation_level=-1)

    def test_immutable(self) -> None:
        issue = make_issue()
        with pytest.raises(AttributeError):
            issue.title = "Changed"  # type: ignore[misc]

    def test_status_transitions(self) -> None:
        issue = make_issue()
        assert issue.can_transition_to("in_progress")
        assert issue.can_transition_to("escalated")
        # closed → reopen is allowed (reopened_at recorded by the service)
        closed = make_issue(status="closed")
        assert closed.can_transition_to("open")
        resolved = make_issue(status="resolved")
        assert resolved.can_transition_to("open")
        # ISSUE_TYPES and ISSUE_STATUSES are intentionally different
        # vocabularies; the transition table must never point outside the
        # status vocabulary.
        assert all(
            target in ISSUE_STATUSES
            for targets in _ISSUE_TRANSITIONS.values()
            for target in targets
        )

    def test_vocabularies(self) -> None:
        assert set(ISSUE_TYPES) == {"defect", "exception", "escalation"}
        assert set(ISSUE_SEVERITIES) == {"low", "medium", "high", "critical"}
        assert set(ISSUE_STATUSES) == {
            "open", "in_progress", "on_hold", "escalated", "resolved", "closed"
        }
