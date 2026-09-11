"""CarbonTally internal operations workflow (spec §17).

Capability tests for operator, reviewer, QC, staff admin, system admin.
Reviewer is NOT admin; only approved admin/system-admin capabilities may
create users or manage roles where that is the agreed policy.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_operations_workflow() -> Workflow:
    return Workflow(
        key="operations",
        label="Internal operations capabilities & boundaries",
        personas=["internal_operator", "internal_reviewer", "internal_qc",
                  "staff_admin", "system_admin"],
        description="Capability boundaries across the ops control plane.",
        steps=[
            step("login", "200", "internal_operator"),
            step("ops_dashboard", "200", "internal_operator"),
            step("data_entry_queue", "200", "internal_operator"),
            step("extract_item", "200", "internal_operator"),
            step("map_item", "200", "internal_operator"),
            step("validate_item", "200", "internal_reviewer", description="reviewer can validate"),
            step("review_queue", "200", "internal_reviewer"),
            step("qc_queue", "200", "internal_qc"),
            step("operator_queue", "403", "internal_reviewer", description="reviewer must NOT run the operator queue"),
            step("calculate_item", "403", "internal_reviewer", description="reviewer must NOT calculate"),
            step("calculate_item", "200", "internal_operator"),
            step("staff_roster", "200", "staff_admin"),
            step("roles", "200", "staff_admin"),
            step("entities", "200", "staff_admin"),
            step("retention_read", "200", "staff_admin"),
            step("commercial_read", "200", "staff_admin"),
            step("audit_read", "200", "staff_admin"),
            step("retention_read", "200", "system_admin", description="OPS-6 regression: sysadmin reaches admin config"),
            step("commercial_read", "200", "system_admin"),
            step("audit_read", "200", "system_admin"),
            step("retention_read", "403", "internal_operator", description="operator denied"),
            step("retention_read", "403", "internal_reviewer", description="reviewer denied"),
            step("retention_read", "403", "internal_qc", description="QC denied"),
        ],
        checks=[
            "reviewer_not_admin",
            "staff_not_staff_admin",
            "staff_admin_can_admin",
            "system_admin_can_admin",
            "user_and_role_management_gated_to_admin",
        ],
    )


OperationsWorkflow = build_operations_workflow()
