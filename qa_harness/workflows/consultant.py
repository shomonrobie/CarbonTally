"""Consultant workflow (spec §15).

Consultants are first-class CarbonTally operators. This workflow specifically
targets the historical problem: "Consultant can log in but cannot actually
operate their customers" (CON-1..3).
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_consultant_workflow() -> Workflow:
    return Workflow(
        key="consultant",
        label="Consultant operating a customer end-to-end",
        personas=["consultant"],
        description=(
            "Detects CON-1..3: consultant must be able to create customers and "
            "operate them. Every action must be scoped to the ACTIVE client."
        ),
        steps=[
            step("login", "200", "consultant"),
            step("consultant_dashboard", "200", "consultant", description="/consultant landing"),
            step("client_portfolio", "200", "consultant", description="list of client orgs"),
            step("create_customer", "201", "consultant", description="onboard a new customer org (D35 self-service)"),
            step("manage_customer", "200", "consultant", description="org profile / settings"),
            step("create_team_member", "201", "consultant", description="consultant firm member"),
            step("assign_team", "200", "consultant", description="assign team to client"),
            step("select_client", "200", "consultant", description="switch ACTIVE client"),
            step("enter_client_workspace", "200", "consultant", description="client workspace with active-client banner"),
            step("upload_document", "201", "consultant", description="upload for the active client"),
            step("drive_processing", "200", "consultant", description="extract/map/validate/calculate"),
            step("reporting", "200", "consultant", description="client reports"),
            step("messaging", "200", "consultant", description="client messaging"),
        ],
        checks=[
            "active_client_isolation",           # CON-5: switching client rescopes everything
            "default_active_client_usable",      # CON-6 regression: no dead-end landing
            "cross_portfolio_isolation",         # consultant 1 vs 2 (P0)
            "consultant_team_boundaries",
        ],
    )


ConsultantWorkflow = build_consultant_workflow()
