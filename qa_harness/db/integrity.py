"""Database integrity audit (read-only).

Encodes the integrity rules from spec §8:

* orphan records
* duplicate business keys
* invalid foreign keys
* impossible status combinations
* missing relationships
* duplicate memberships
* duplicate conversation participants
* broken evidence links
* calculation snapshots without valid source items
* emissions records without valid calculation evidence

Each rule is a parameterized SELECT; the run layer executes them against the
target database and reports violations as findings. No writes ever occur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class IntegrityRule:
    id: str
    name: str
    description: str
    table: str
    # SQL that returns violating rows. Must be read-only (SELECT).
    sql: str = ""
    severity: str = "P2"
    # Optional threshold: only report when the violation count exceeds it.
    report_threshold: int = 0
    # When True, a row count of the violation query is the only evidence needed.
    count_only: bool = False

    def render(self, params: Optional[Dict[str, Any]] = None) -> str:
        if not self.sql:
            raise ValueError(f"rule {self.id} has no SQL")
        return self.sql.format(**(params or {}))


def _orphan(rule_id: str, table: str, child_col: str, parent_table: str,
            parent_col: str = "id", severity: str = "P2") -> IntegrityRule:
    return IntegrityRule(
        id=rule_id,
        name=f"Orphan {table}.{child_col}",
        description=f"Rows in {table} referencing a missing {parent_table}.{parent_col}.",
        table=table,
        sql=(
            f"SELECT t.id FROM {table} t LEFT JOIN {parent_table} p "
            f"ON p.{parent_col} = t.{child_col} WHERE t.{child_col} IS NOT NULL AND p.{parent_col} IS NULL LIMIT 100;"
        ),
        severity=severity,
        count_only=True,
    )


def _duplicate_business_key(rule_id: str, table: str, columns: List[str],
                            severity: str = "P2") -> IntegrityRule:
    cols = ", ".join(columns)
    return IntegrityRule(
        id=rule_id,
        name=f"Duplicate business key in {table} ({cols})",
        description=f"More than one row per ({cols}) in {table} where the pair should be unique.",
        table=table,
        sql=(
            f"SELECT {cols}, COUNT(*) AS n FROM {table} "
            f"GROUP BY {cols} HAVING COUNT(*) > 1 LIMIT 100;"
        ),
        severity=severity,
        count_only=True,
    )


def _duplicate_pair(rule_id: str, table: str, a: str, b: str,
                    severity: str = "P2", name: str = "") -> IntegrityRule:
    return IntegrityRule(
        id=rule_id,
        name=name or f"Duplicate ({a},{b}) in {table}",
        description=f"Rows in {table} where the ({a},{b}) pair is duplicated — the "
                    f"application code assumes uniqueness (ON CONFLICT upserts).",
        table=table,
        sql=(
            f"SELECT {a}, {b}, COUNT(*) AS n FROM {table} "
            f"GROUP BY {a}, {b} HAVING COUNT(*) > 1 LIMIT 100;"
        ),
        severity=severity,
        count_only=True,
    )


def _impossible_status(rule_id: str, table: str, where: str, severity: str = "P3",
                       name: str = "") -> IntegrityRule:
    return IntegrityRule(
        id=rule_id,
        name=name or f"Impossible status combination in {table}",
        description=f"Rows matching a logically impossible state: {where}.",
        table=table,
        sql=f"SELECT id FROM {table} WHERE {where} LIMIT 100;",
        severity=severity,
        count_only=True,
    )


def build_standard_rules() -> List[IntegrityRule]:
    """The documented CarbonTally integrity rule set (spec §8)."""
    rules: List[IntegrityRule] = []
    # Orphan records.
    rules.append(_orphan("INT-ORPHAN-1", "organization_files", "organization_id", "organizations", severity="P1"))
    rules.append(_orphan("INT-ORPHAN-2", "organization_members", "organization_id", "organizations", severity="P1"))
    rules.append(_orphan("INT-ORPHAN-3", "organization_members", "user_id", "users", severity="P1"))
    rules.append(_orphan("INT-ORPHAN-4", "upload_batches", "organization_id", "organizations", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-5", "manual_extraction_items", "batch_id", "manual_extraction_batches", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-6", "manual_extraction_items", "file_id", "organization_files", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-7", "consultant_clients", "organization_id", "organizations", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-8", "conversation_participants", "user_id", "users", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-9", "messages", "conversation_id", "conversations", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-10", "messages", "sender_id", "users", severity="P2"))
    rules.append(_orphan("INT-ORPHAN-11", "assets", "facility_id", "facilities", severity="P3"))
    rules.append(_orphan("INT-ORPHAN-12", "staff_profiles", "entity_id", "processing_entities", severity="P2"))
    # Duplicate business keys / pairs.
    rules.append(_duplicate_pair("INT-DUP-1", "organization_members", "organization_id", "user_id", severity="P1",
                                 name="Duplicate organization membership"))
    rules.append(_duplicate_pair("INT-DUP-2", "conversation_participants", "conversation_id", "user_id", severity="P1",
                                 name="Duplicate conversation participant (ON CONFLICT target)"))
    rules.append(_duplicate_pair("INT-DUP-3", "consultant_clients", "consultant_id", "organization_id", severity="P2",
                                 name="Duplicate consultant-client assignment"))
    rules.append(_duplicate_business_key("INT-DUP-4", "emission_factors", ["activity", "unit", "scope", "country", "year"], severity="P3"))
    # Impossible status combinations.
    rules.append(_impossible_status("INT-STATE-1", "issues", "status = 'resolved' AND resolved_at IS NULL",
                                    name="Resolved issue without resolved_at"))
    rules.append(_impossible_status("INT-STATE-2", "processing_queue",
                                    "status = 'completed' AND stage NOT IN ('calculated','approved','completed')",
                                    name="Completed queue row on an impossible stage"))
    rules.append(_impossible_status("INT-STATE-3", "report_versions",
                                    "status = 'completed' AND generated_at IS NULL",
                                    name="Completed report without generated_at"))
    rules.append(_impossible_status("INT-STATE-4", "customer_factors",
                                    "status = 'active' AND approved_by IS NULL",
                                    name="Active customer factor without approver (unless PO self-approval)"))
    rules.append(_impossible_status("INT-STATE-5", "manual_extraction_items",
                                    "status = 'calculated' AND calculated_emissions_kg_co2e IS NULL",
                                    name="Calculated item without emissions value"))
    rules.append(_impossible_status("INT-STATE-6", "organizations",
                                    "status = 'active' AND created_at IS NULL",
                                    name="Active organization without created_at"))
    # Missing relationships.
    rules.append(IntegrityRule(
        id="INT-MISS-1",
        name="Organization without any members",
        description="Organizations that have no organization_members rows (operationally dead orgs).",
        table="organizations",
        sql=(
            "SELECT o.id FROM organizations o LEFT JOIN organization_members om "
            "ON om.organization_id = o.id WHERE om.id IS NULL LIMIT 100;"
        ),
        severity="P3",
        count_only=True,
    ))
    # Broken evidence links.
    rules.append(IntegrityRule(
        id="INT-EVD-1",
        name="Calculation snapshot without source_item_id",
        description="Evidence chain terminates: snapshot has no source item (historical ISC-1).",
        table="calculation_snapshots",
        sql="SELECT id FROM calculation_snapshots WHERE source_item_id IS NULL LIMIT 100;",
        severity="P1",
        count_only=True,
    ))
    rules.append(IntegrityRule(
        id="INT-EVD-2",
        name="Emissions log without valid calculation evidence",
        description="Emissions rows whose snapshot_id does not resolve to a calculation_snapshot.",
        table="emissions_logs",
        sql=(
            "SELECT l.id FROM emissions_logs l LEFT JOIN calculation_snapshots s "
            "ON s.id = l.snapshot_id WHERE l.snapshot_id IS NOT NULL AND s.id IS NULL LIMIT 100;"
        ),
        severity="P1",
        count_only=True,
    ))
    rules.append(IntegrityRule(
        id="INT-EVD-3",
        name="Emissions log without snapshot at all",
        description="Emissions rows with no calculation evidence (snapshot_id NULL).",
        table="emissions_logs",
        sql="SELECT id FROM emissions_logs WHERE snapshot_id IS NULL LIMIT 100;",
        severity="P2",
        count_only=True,
    ))
    return rules


class IntegrityAudit:
    """Executes integrity rules and aggregates violations."""

    def __init__(self, connection: Any, rules: Optional[List[IntegrityRule]] = None) -> None:
        self._conn = connection
        self.rules = rules or build_standard_rules()

    def run(self) -> Dict[str, int]:
        """Return {rule_id: violation_count}. Read-only."""
        results: Dict[str, int] = {}
        for rule in self.rules:
            cursor = self._conn.cursor()
            try:
                cursor.execute(rule.render())
                rows = cursor.fetchall()
                results[rule.id] = len(rows) if not rule.count_only else (rows[0][0] if rows else 0)
            except Exception:
                results[rule.id] = -1  # rule could not run (e.g. missing table)
            finally:
                cursor.close()
        return results

    def violations_above_threshold(self, results: Dict[str, int]) -> List[IntegrityRule]:
        return [
            rule for rule in self.rules
            if results.get(rule.id, 0) > rule.report_threshold
        ]
