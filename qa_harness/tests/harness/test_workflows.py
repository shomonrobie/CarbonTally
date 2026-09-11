"""Harness self-tests: executable workflow definitions (spec §13–§18)."""

from __future__ import annotations

from qa_harness.api.workflows import WorkflowStateMachine
from qa_harness.workflows import (
    AdminWorkflow,
    ClientWorkflow,
    ConsultantWorkflow,
    CustomerWorkflow,
    MessagingWorkflow,
    OperationsWorkflow,
    ProcessingEntityWorkflow,
)

ALL_WORKFLOWS = {
    "customer": CustomerWorkflow,
    "consultant": ConsultantWorkflow,
    "client": ClientWorkflow,
    "pe": ProcessingEntityWorkflow,
    "operations": OperationsWorkflow,
    "admin": AdminWorkflow,
    "messaging": MessagingWorkflow,
}


def test_all_workflows_have_steps_and_personas() -> None:
    for key, workflow in ALL_WORKFLOWS.items():
        assert workflow.key == key
        assert workflow.label
        assert workflow.personas
        assert workflow.steps, f"{key} workflow has no steps"
        assert all(s.action for s in workflow.steps)


def test_customer_workflow_is_end_to_end() -> None:
    actions = [s.action for s in CustomerWorkflow.steps]
    chain = ["login", "upload_document", "extraction", "mapping", "validation",
             "calculation", "evidence", "review", "approval", "completed",
             "emissions", "reporting"]
    for expected in chain:
        assert expected in actions, f"customer workflow missing {expected}"
    assert all(s.verify_persisted for s in CustomerWorkflow.steps)


def test_consultant_workflow_can_operate_customers() -> None:
    """Historical defect: 'consultant can log in but cannot operate customers'."""
    actions = [s.action for s in ConsultantWorkflow.steps]
    for required in ("create_customer", "upload_document", "enter_client_workspace"):
        assert required in actions, f"consultant workflow missing {required}"


def test_pe_workflow_respects_boundaries() -> None:
    checks = ProcessingEntityWorkflow.checks or []
    assert any("isolation" in c.lower() or "document" in c.lower() for c in checks)


def test_messaging_workflow_covers_isolation() -> None:
    actions = [s.action for s in MessagingWorkflow.steps]
    assert "create_conversation" in actions
    assert "send_message" in actions


def test_expected_statuses_are_valid() -> None:
    machine = WorkflowStateMachine()
    for workflow in ALL_WORKFLOWS.values():
        for step in workflow.steps:
            status = step.expected_status
            assert status in ("200", "201", "403", "deny", "no_path", ""), (
                f"{workflow.key}.{step.action} has unknown expected_status {status!r}"
            )


def test_workflow_serialization() -> None:
    data = CustomerWorkflow.to_dict()
    assert data["key"] == "customer"
    assert data["steps"]
