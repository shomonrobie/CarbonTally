"""Processing Entity workflow (spec §16).

PE Manager and PE Staff/Operator operate within their own entity's assigned
work. The harness must explicitly verify that PE users cannot access
prohibited customer source documents (D20 no-download boundary) and that
cross-entity isolation holds.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_pe_workflow() -> Workflow:
    return Workflow(
        key="pe",
        label="Processing Entity workspace & boundaries",
        personas=["pe_manager", "pe_staff"],
        description=(
            "PE staff see only entity-assigned work; no customer source "
            "document download path; no cross-entity access."
        ),
        steps=[
            step("login", "200", "pe_manager"),
            step("pe_workspace", "200", "pe_manager", description="/ops entity surface"),
            step("entity_batch_list", "200", "pe_manager", description="PE-2 regression: manager sees assigned work"),
            step("entity_performance", "200", "pe_manager"),
            step("assigned_batch_visibility", "200", "pe_staff"),
            step("manual_extraction", "200", "pe_staff", description="source viewer + lines + save"),
            step("processing", "200", "pe_staff", description="map/validate within entity"),
            step("calculate", "200", "pe_staff", description="start('calculation') → calculate"),
            step("allowed_messaging", "200", "pe_staff"),
            step("customer_document_access", "deny", "pe_staff", description="org-scoped docs denied"),
            step("customer_document_download", "no_path", "pe_staff", description="D20 no-download boundary"),
            step("customer_org_conversation", "403", "pe_staff", description="PE must not post into customer-org convos"),
            step("other_entity_work", "403", "pe_staff", description="cross-entity isolation"),
            step("internal_ops_workspace", "deny", "pe_staff", description="PE must not reach internal ops control plane"),
        ],
        checks=[
            "pe_cannot_access_prohibited_customer_source_documents",
            "pe_manager_can_see_assigned_work",      # PE-2 regression
            "cross_pe_isolation",                    # entity A vs B
            "no_download_path_for_customer_documents",
        ],
    )


ProcessingEntityWorkflow = build_pe_workflow()
