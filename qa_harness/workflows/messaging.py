"""Messaging workflow (spec §22).

Conversation creation, participants, messages, realtime delivery, unread
state, notifications and isolation boundaries. Also verifies the visitor-only
assistant is NOT used as the authenticated messaging mechanism.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_messaging_workflow() -> Workflow:
    return Workflow(
        key="messaging",
        label="Authenticated messaging (N1)",
        personas=["customer_owner", "customer_admin", "consultant",
                  "pe_manager", "pe_staff"],
        description="N1 realtime messaging with strict isolation boundaries.",
        steps=[
            step("create_conversation", "201", "customer_owner", description="MSG-1 regression: creation must work"),
            step("add_participants", "200", "customer_owner"),
            step("send_message", "200", "customer_owner"),
            step("receive_message", "200", "customer_member", description="participant receives"),
            step("realtime_delivery", "200", "customer_owner", description="Realtime subscription observed"),
            step("unread_state", "200", "customer_member"),
            step("notifications", "200", "customer_owner", description="bell via API surface (NOT-1 regression)"),
            step("cross_org_conversation", "403", "customer_owner", description="cannot open conversation with other org"),
            step("cross_client_conversation", "403", "client_owner", description="client cannot open sibling-client convo"),
            step("pe_to_customer_conversation", "403", "pe_staff", description="PE must not post into customer-org convos"),
            step("visitor_assistant_as_messaging", "deny", "customer_owner",
                 description="assistant widget must not be the authenticated messaging mechanism"),
        ],
        checks=[
            "cross_org_isolation",
            "cross_client_isolation",
            "pe_boundaries",
            "internal_messaging",
            "authenticated_user_messaging_only",
            "visitor_assistant_not_used_as_messaging",
        ],
    )


MessagingWorkflow = build_messaging_workflow()
