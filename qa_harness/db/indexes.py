"""Index expectations and coverage audit (read-only).

Operational tables that grow (queues, messages, emissions_logs, issues,
uploads) need indexes on their filter/join columns. The audit compares the
probed index set against documented expectations and flags missing indexes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qa_harness.db.schema_inventory import TableInfo


@dataclass
class ExpectedIndex:
    table: str
    column: str
    name: str
    reason: str = ""
    severity: str = "P2"


def build_expected_indexes() -> List[ExpectedIndex]:
    """Documented index expectations for high-growth operational tables."""
    return [
        ExpectedIndex("organization_files", "organization_id", "idx_org_files_org",
                      "Every org-scoped document query filters by organization_id.", "P1"),
        ExpectedIndex("upload_batches", "organization_id", "idx_upload_batches_org", "", "P2"),
        ExpectedIndex("upload_batches", "status", "idx_upload_batches_status",
                      "Queue scans filter on status.", "P2"),
        ExpectedIndex("manual_extraction_items", "batch_id", "idx_extract_items_batch", "", "P2"),
        ExpectedIndex("manual_extraction_items", "file_id", "idx_extract_items_file",
                      "Document→emissions reverse lookup joins on file_id (D33).", "P1"),
        ExpectedIndex("manual_extraction_items", "status", "idx_extract_items_status", "", "P2"),
        ExpectedIndex("emissions_logs", "organization_id", "idx_emissions_logs_org",
                      "Dashboard/reports query emissions per organization.", "P1"),
        ExpectedIndex("emissions_logs", "snapshot_id", "idx_emissions_logs_snapshot",
                      "Evidence chain lookup.", "P2"),
        ExpectedIndex("calculation_snapshots", "source_item_id", "idx_calc_snapshots_source",
                      "Document→emissions reverse lookup (D33).", "P1"),
        ExpectedIndex("issues", "organization_id", "idx_issues_org", "Dashboard attention counts.", "P2"),
        ExpectedIndex("issues", "status", "idx_issues_status", "Issue triage queue.", "P3"),
        ExpectedIndex("messages", "conversation_id", "idx_messages_conversation", "Thread reads.", "P1"),
        ExpectedIndex("conversation_participants", "user_id", "idx_conv_participants_user",
                      "Inbox queries per user.", "P2"),
        ExpectedIndex("notifications", "recipient_id", "idx_notifications_recipient", "Bell queries.", "P2"),
        ExpectedIndex("processing_queue", "stage", "idx_processing_queue_stage", "Stage queues.", "P2"),
        ExpectedIndex("processing_queue", "entity_id", "idx_processing_queue_entity",
                      "PE-scoped batch lists (PE-2 context).", "P2"),
        ExpectedIndex("report_versions", "organization_id", "idx_report_versions_org", "", "P2"),
        ExpectedIndex("vehicles", "organization_id", "idx_vehicles_org", "", "P2"),
    ]


class IndexAudit:
    def __init__(self, expected: Optional[List[ExpectedIndex]] = None) -> None:
        self.expected = expected or build_expected_indexes()

    def missing_indexes(self, probed: Dict[str, TableInfo]) -> List[ExpectedIndex]:
        """Return expected indexes not present in the probed inventory.

        Matching is by column presence in any index on that table. Index names
        vary across environments, so the exact column name OR its base form
        (trailing ``_id`` stripped) counts as coverage — e.g. an index named
        ``idx_messages_conversation`` covers ``conversation_id``.
        """
        missing: List[ExpectedIndex] = []
        for exp in self.expected:
            info = probed.get(exp.table)
            if info is None:
                continue  # table absent — reported by SchemaInventory
            base = exp.column[:-3] if exp.column.endswith("_id") else exp.column
            # Base-form matching only for meaningful tokens (>= 4 chars) to
            # avoid 2–3 char fragments matching unrelated index names.
            base = base if len(base) >= 4 else ""
            covered = any(
                exp.column in name.lower() or (base and base in name.lower())
                for name in info.indexes
            )
            if not covered:
                missing.append(exp)
        return missing
