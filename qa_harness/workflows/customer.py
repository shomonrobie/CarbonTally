"""Customer workflow (spec §13, §18).

upload → storage → file record → processing job → ingestion → extraction →
mapping → validation → calculation → evidence → review → approval →
completed → emissions → reporting. The run layer must verify persisted state
for every step — never rely on UI animations or a spinner.
"""

from __future__ import annotations

from qa_harness.workflows.base import Workflow, step


def build_customer_workflow() -> Workflow:
    return Workflow(
        key="customer",
        label="Customer document → emissions → report",
        personas=["customer_owner", "customer_admin"],
        description=(
            "The primary customer outcome. Every step must persist in the "
            "database; UI animations are not evidence."
        ),
        steps=[
            step("login", "200", "customer_owner", description="password grant → session"),
            step("upload_document", "201", "customer_owner", description="multipart upload → storage object"),
            step("storage_object", "201", "customer_owner", description="object present in documents bucket"),
            step("file_record", "201", "customer_owner", description="organization_files row"),
            step("processing_job", "201", "customer_owner", description="upload_batches / processing_queue row"),
            step("ingestion", "200", "internal_operator", description="ingest stage"),
            step("extraction", "200", "internal_operator", description="extract → extracted"),
            step("mapping", "200", "internal_operator", description="map → mapped"),
            step("validation", "200", "internal_reviewer", description="validate → validated"),
            step("calculation", "200", "internal_operator", description="start('calculation') → calculate → calculated"),
            step("evidence", "200", "internal_operator", description="calculation_snapshot with source_item_id"),
            step("review", "200", "customer_owner", description="customer review queue lists the item"),
            step("approval", "200", "customer_owner", description="approve → customer_approved"),
            step("completed", "200", "internal_operator", description="terminal completed state"),
            step("emissions", "200", "customer_owner", description="emissions_logs row with CO₂e + evidence"),
            step("reporting", "200", "customer_owner", description="report generated from real data with lineage"),
        ],
        checks=[
            "customer_review_approval_gate",       # owner/admin 200; member/viewer 403
            "rejection_requires_reason",
            "document_emissions_reverse_lookup",   # D33: document page shows emissions
            "unit_alias_resolution",               # L ↔ litres (PRC-2 regression)
            "viewer_upload_denied",                # SEC-1 regression
        ],
    )


CustomerWorkflow = build_customer_workflow()
