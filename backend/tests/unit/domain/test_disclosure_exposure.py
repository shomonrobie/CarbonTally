"""Phase 8 B4 — DM-6 drill-down exposure matrix (pure unit tests)."""
from __future__ import annotations

import pytest

from domain.disclosure import DisclosureViolation
from domain.disclosure_exposure import (
    DEPTH_BOUNDED,
    DEPTH_CONTROLLED,
    DEPTH_DENIED,
    DEPTH_FULL,
    assert_drilldown_allowed,
    exposure_for_role,
    project_lines,
    redact_line,
)

LINE = {
    "id": "line-1",
    "line_number": 1,
    "description": "Diesel generator run hours",
    "amount": 1250.5,
    "unit": "litres",
    "document_id": "doc-1",
    "storage_path": "org/doc-1.pdf",
    "signed_url": "https://example.invalid/sig",
    "evidence_hash": "abc123",
}


@pytest.mark.parametrize(
    ("role", "depth"),
    [
        ("owner", DEPTH_FULL),
        ("org_owner", DEPTH_FULL),
        ("admin", DEPTH_FULL),
        ("org_admin", DEPTH_FULL),
        ("viewer", DEPTH_CONTROLLED),
        ("member", DEPTH_CONTROLLED),
        ("user", DEPTH_CONTROLLED),
        ("consultant", DEPTH_BOUNDED),
        ("consultant_member", DEPTH_BOUNDED),
        ("unknown_role", DEPTH_DENIED),
        ("", DEPTH_DENIED),
        (None, DEPTH_DENIED),
    ],
)
def test_matrix_follows_dm6(role, depth) -> None:
    assert exposure_for_role(role).depth == depth


def test_processing_entity_is_denied_even_with_a_customer_role() -> None:
    rule = exposure_for_role("owner", is_entity_staff=True)
    assert rule.depth == DEPTH_DENIED
    assert "Processing Entity" in rule.rationale


def test_internal_staff_is_denied() -> None:
    assert exposure_for_role("admin", is_internal_staff=True).depth == DEPTH_DENIED
    assert exposure_for_role("staff", is_internal_staff=True).depth == DEPTH_DENIED


def test_denied_raises_never_returns_partial() -> None:
    with pytest.raises(DisclosureViolation):
        assert_drilldown_allowed(exposure_for_role("pe_staff", is_entity_staff=True))


def test_full_depth_returns_every_field() -> None:
    assert redact_line(LINE, exposure_for_role("owner")) == LINE


def test_controlled_depth_hides_document_and_storage_references() -> None:
    out = redact_line(LINE, exposure_for_role("viewer"))
    assert "amount" in out  # a viewer may see the quantities
    assert "description" in out
    for key in ("document_id", "storage_path", "signed_url", "evidence_hash"):
        assert key not in out
    assert out["redacted_fields"] == [
        "document_id",
        "evidence_hash",
        "signed_url",
        "storage_path",
    ]


def test_bounded_depth_hides_quantities_too() -> None:
    out = redact_line(LINE, exposure_for_role("consultant"))
    for key in ("amount", "unit", "document_id", "storage_path", "signed_url"):
        assert key not in out
    assert out["id"] == "line-1"
    assert out["line_number"] == 1
    assert out["description"] == "Diesel generator run hours"


def test_unknown_keys_are_withheld_by_default_below_full() -> None:
    row = dict(LINE)
    row["future_sensitive_column"] = "?"
    owner = redact_line(row, exposure_for_role("owner"))
    viewer = redact_line(row, exposure_for_role("viewer"))
    assert "future_sensitive_column" in owner
    # Denylist semantics: an unrecognised non-structural column is not exposed.
    assert "future_sensitive_column" in viewer["redacted_fields"]


def test_project_lines_refuses_denied_callers() -> None:
    with pytest.raises(DisclosureViolation):
        project_lines([LINE], exposure_for_role(None))


def test_project_lines_projects_every_row() -> None:
    rows = project_lines([LINE, LINE], exposure_for_role("consultant"))
    assert len(rows) == 2
    assert all("document_id" not in r for r in rows)
