"""Constraint expectations (read-only).

Encodes the documented constraint model from the repo schema/migrations:

* every table has a primary key,
* ``conversation_participants(conversation_id, user_id)`` is UNIQUE (the
  messaging upsert depends on it — historical MSG-1),
* ``organization_members(organization_id, user_id)`` is UNIQUE,
* ``consultant_clients(consultant_id, organization_id)`` is UNIQUE,
* ``facilities`` has a postcode-or-eircode CHECK,
* ``vehicles`` exists (historical MD-2 migration-gap regression target).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from qa_harness.db.schema_inventory import TableInfo


@dataclass
class ExpectedConstraint:
    kind: str            # pk | unique_pair | unique | check | table_exists
    table: str
    columns: List[str] = field(default_factory=list)
    name: str = ""
    severity: str = "P1"
    reason: str = ""


def build_expected_constraints() -> List[ExpectedConstraint]:
    return [
        ExpectedConstraint("pk", "conversation_participants", name="PK conversation_participants",
                           reason="every table needs a primary key"),
        ExpectedConstraint("unique_pair", "conversation_participants",
                           columns=["conversation_id", "user_id"],
                           name="UNIQUE (conversation_id, user_id)",
                           reason="messaging upsert ON CONFLICT target (historical MSG-1)", severity="P1"),
        ExpectedConstraint("unique_pair", "organization_members",
                           columns=["organization_id", "user_id"],
                           name="UNIQUE (organization_id, user_id)",
                           reason="duplicate membership prevention", severity="P1"),
        ExpectedConstraint("unique_pair", "consultant_clients",
                           columns=["consultant_id", "organization_id"],
                           name="UNIQUE (consultant_id, organization_id)",
                           reason="duplicate client assignment prevention", severity="P2"),
        ExpectedConstraint("check", "facilities",
                           columns=["postcode", "eircode"],
                           name="facilities_postcode_or_eircode_check",
                           reason="DB CHECK requires postcode OR eircode (historical MD-1)", severity="P2"),
        ExpectedConstraint("table_exists", "vehicles", name="vehicles table",
                           reason="migration v3m7 must be applied (historical MD-2)", severity="P1"),
        ExpectedConstraint("pk", "emissions_logs", name="PK emissions_logs", severity="P2"),
        ExpectedConstraint("pk", "calculation_snapshots", name="PK calculation_snapshots", severity="P2"),
        ExpectedConstraint("pk", "organization_files", name="PK organization_files", severity="P2"),
    ]


class ConstraintAudit:
    def __init__(self, expected: Optional[List[ExpectedConstraint]] = None) -> None:
        self.expected = expected or build_expected_constraints()

    def violations(self, probed: Dict[str, TableInfo]) -> List[ExpectedConstraint]:
        problems: List[ExpectedConstraint] = []
        for exp in self.expected:
            if exp.kind == "table_exists":
                if exp.table not in probed:
                    problems.append(exp)
                continue
            info = probed.get(exp.table)
            if info is None:
                continue  # missing table is reported by SchemaInventory
            if exp.kind == "pk":
                if not info.primary_key:
                    problems.append(exp)
            elif exp.kind == "unique_pair":
                pair = sorted(exp.columns)
                if not any(sorted(u) == pair for u in info.unique_constraints):
                    problems.append(exp)
            elif exp.kind == "check":
                if not any(exp.columns[0] in c or exp.columns[1] in c for c in info.check_constraints):
                    problems.append(exp)
        return problems
