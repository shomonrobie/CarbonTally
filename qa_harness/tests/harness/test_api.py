"""Harness self-tests: API discovery, authorization matrix, security, state machines."""

from __future__ import annotations

import json
from pathlib import Path

from qa_harness.api.authorization import AuthorizationMatrix, build_standard_matrix
from qa_harness.api.inventory import EndpointInventory
from qa_harness.api.security import ApiSecurityAudit, build_security_boundaries
from qa_harness.api.workflows import WorkflowStateMachine

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _openapi() -> dict:
    return json.loads((FIXTURES / "tiny_openapi.json").read_text(encoding="utf-8"))


def test_inventory_build() -> None:
    inventory = EndpointInventory(_openapi(), api_prefix="/api/v3")
    endpoints = inventory.build()
    assert len(endpoints) == 4
    assert len(inventory.v3_endpoints()) == 3


def test_inventory_auth_required() -> None:
    inventory = EndpointInventory(_openapi(), api_prefix="/api/v3")
    by_key = {e.key: e for e in inventory.build()}
    assert by_key["GET /api/v3/orgs"].auth_required is True
    assert by_key["GET /healthz"].auth_required is False


def test_inventory_by_tag() -> None:
    inventory = EndpointInventory(_openapi(), api_prefix="/api/v3")
    orgs = inventory.by_tag("organizations")
    assert len(orgs) == 2


def test_unexpected_flags_only_5xx() -> None:
    inventory = EndpointInventory(_openapi(), api_prefix="/api/v3")
    inventory.build()
    inventory.endpoints[0].expected_status = 200
    inventory.endpoints[0].actual_status = 403  # legitimate → not flagged
    inventory.endpoints[1].expected_status = 201
    inventory.endpoints[1].actual_status = 500  # always flagged
    flagged = inventory.unexpected()
    assert [e.path for e in flagged] == ["/api/v3/orgs"]


def test_authorization_matrix_documented() -> None:
    matrix = AuthorizationMatrix()
    expectations = matrix.expectations
    assert len(expectations) >= 25
    expected_values = {e.expected for e in expectations}
    assert expected_values <= {"ALLOW", "DENY", "PO DECISION REQUIRED"}


def test_authorization_classify() -> None:
    matrix = AuthorizationMatrix()
    # Customer A → Customer B document must be DENY: a 403 satisfies it.
    matrix.record("AUTHZ-1", 403)
    assert matrix.expectations[0].status == "PASS"
    # A 200 here would be a failure (cross-tenant leak).
    matrix.record("AUTHZ-1", 200)
    assert matrix.expectations[0].status == "FAIL"


def test_authorization_po_decision() -> None:
    matrix = AuthorizationMatrix()
    matrix.record("AUTHZ-26", 403)
    po = matrix.po_decisions()
    assert [e.id for e in po] == ["AUTHZ-26"]
    assert po[0].status == "PO DECISION REQUIRED"


def test_authorization_failures_and_po() -> None:
    matrix = AuthorizationMatrix()
    # Default state: no assertion has run, so nothing is FAIL and nothing is
    # PO DECISION REQUIRED yet (both are filled only after recording probes).
    assert matrix.failures() == []
    assert matrix.po_decisions() == []
    matrix.record("AUTHZ-26", 200)
    assert [e.id for e in matrix.po_decisions()] == ["AUTHZ-26"]


def test_security_boundaries_documented() -> None:
    audit = ApiSecurityAudit()
    boundaries = audit.boundaries
    assert any(b.id == "SECB-5" for b in boundaries)   # cross-org P0
    assert any(b.id == "SECB-11" for b in boundaries)  # PE no document path
    assert any(b.severity == "P0" for b in boundaries)


def test_security_boundary_evaluate_violation() -> None:
    audit = ApiSecurityAudit()
    # SECB-5 expects DENIED; observing ALLOWED is a violation.
    boundary = audit.evaluate("SECB-5", "ALLOWED")
    assert boundary is not None
    assert audit.violations() == [boundary]


def test_security_boundary_pass() -> None:
    audit = ApiSecurityAudit()
    audit.evaluate("SECB-1", "DENIED")
    assert audit.violations() == []


def test_state_machine_valid_transitions() -> None:
    machine = WorkflowStateMachine()
    assert "extracting" in machine.legal_next("queued")
    assert "review" in machine.legal_next("calculated")
    assert "approved" in machine.legal_next("review")
    assert "retry" in machine.legal_next("failed")


def test_state_machine_invalid_transitions() -> None:
    machine = WorkflowStateMachine()
    assert "completed" not in machine.legal_next("uploaded")
    assert "approved" not in machine.legal_next("extracting")
    assert "uploaded" not in machine.legal_next("completed")


def test_state_machine_check() -> None:
    machine = WorkflowStateMachine()
    legal = machine.check("item-1", "queued", "extract")
    assert legal.legal is True
    illegal = machine.check("item-1", "uploaded", "approve")
    assert illegal.legal is False
    assert "not documented" in illegal.note


def test_state_machine_pipeline_covers_chain() -> None:
    machine = WorkflowStateMachine()
    path = machine.pipeline("queued", "approved")
    assert path[0] == "queued"
    assert "extracting" in path
    assert "mapping" in path
    assert "validating" in path
    assert "calculating" in path
    assert path[-1] == "approved"
    # The review gate is a documented next stage from calculated.
    assert "review" in machine.legal_next("calculated")
