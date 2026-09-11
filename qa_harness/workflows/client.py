"""Consultant client workflow.

A client (consultant-managed customer organisation) must be able to review and
approve its own emissions within its own org boundary while the consultant
operates on its behalf — with strict client-to-client isolation.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_client_workflow() -> Workflow:
    return Workflow(
        key="client",
        label="Consultant client lifecycle & isolation",
        personas=["client_owner", "consultant"],
        description=(
            "Client owners are customer orgs owned/operated via a consultant. "
            "Verify the client can see its own data, approve its own items, "
            "message its consultant, and cannot see sibling clients."
        ),
        steps=[
            step("login", "200", "client_owner"),
            step("client_dashboard", "200", "client_owner", description="/home for the client org"),
            step("view_documents", "200", "client_owner"),
            step("review_and_approve", "200", "client_owner", description="client approval gate"),
            step("view_emissions", "200", "client_owner"),
            step("generate_report", "200", "client_owner"),
            step("message_consultant", "200", "client_owner", description="client ↔ consultant messaging"),
        ],
        checks=[
            "client_a_cannot_read_client_b",      # same-consultant sibling isolation
            "client_cannot_access_consultant_workspace",
            "client_data_scoped_to_own_org",
        ],
    )


ClientWorkflow = build_client_workflow()
