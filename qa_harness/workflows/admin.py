"""Admin control-plane workflow (spec §17).

Staff admin and system admin capabilities over the administrative control
plane: staff management, role management, billing configuration, retention
configuration, audit log.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_admin_workflow() -> Workflow:
    return Workflow(
        key="admin",
        label="Admin control plane",
        personas=["staff_admin", "system_admin"],
        description="Approved admin capabilities only; no capability creep.",
        steps=[
            step("login", "200", "staff_admin"),
            step("staff_management", "200", "staff_admin", description="roster + create + role select"),
            step("role_management", "200", "staff_admin", description="staff_roles control"),
            step("billing_config", "200", "staff_admin", description="commercial billing mode + plans"),
            step("retention_config", "200", "staff_admin", description="retention read/write"),
            step("audit_log", "200", "staff_admin", description="audit console"),
            step("system_admin_retention", "200", "system_admin", description="OPS-6 regression"),
            step("system_admin_commercial", "200", "system_admin", description="OPS-6 regression"),
            step("system_admin_audit", "200", "system_admin", description="ISC-10 regression"),
        ],
        checks=[
            "admin_surfaces_render_from_real_endpoints",
            "sysadmin_reaches_admin_gated_surfaces",
            "no_stray_test_roles_in_role_selector",   # SA-4 regression
        ],
    )


AdminWorkflow = build_admin_workflow()
