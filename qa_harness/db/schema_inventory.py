"""Database schema inventory (read-only).

Two layers:

* :class:`SchemaProbe` — the SQL the harness executes against Postgres
  (information_schema + pg_catalog) to enumerate tables, columns, types,
  keys, constraints, indexes, triggers, views, functions and RLS state.
* :class:`SchemaInventory` — the documented EXPECTED inventory (tables and
  key columns) encoded from the repo schema/migrations; the run layer
  compares probe results against this.

Probing requires a read-only connection; without one the module reports
``SKIPPED — TOOL UNAVAILABLE`` (no database reachable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Documented CarbonTally tables (from repo migrations + schema files).
EXPECTED_TABLES: List[str] = [
    "organizations", "users", "organization_members",
    "consultant_profiles", "consultant_clients", "consultant_firm_members",
    "staff_profiles", "staff_roles", "processing_entities",
    "organization_files", "upload_batches",
    "manual_extraction_batches", "manual_extraction_items",
    "emission_factors", "customer_factors", "factor_aliases",
    "calculation_snapshots", "emissions_logs", "issues",
    "report_versions", "report_generation_queue", "report_templates",
    "conversations", "conversation_participants", "messages",
    "notifications", "notification_delivery",
    "billing_plans", "billing_orders", "billing_credit_ledger",
    "billing_commercial_config", "customer_subscriptions",
    "facilities", "assets", "suppliers", "vehicles",
    "processing_queue", "processing_assignments", "processing_audit_trail",
    "customer_review_log", "approval_decisions", "approval_requests",
    "audit_logs", "domain_events", "qc_checks", "qc_errors", "qc_checklists",
    "sla_definitions", "sla_compliance", "units", "activity_categories",
    "document_types", "document_type_categories", "pending_invites",
    "user_invitations", "system_settings", "storage_buckets",
]

# Key tables and the columns the harness checks for presence (documented).
KEY_TABLE_COLUMNS: Dict[str, List[str]] = {
    "organizations": ["id", "name", "created_at"],
    "organization_members": ["organization_id", "user_id", "role", "status"],
    "consultant_clients": ["consultant_id", "organization_id", "status", "active"],
    "staff_profiles": ["user_id", "staff_role", "entity_id", "is_admin"],
    "processing_entities": ["id", "name", "status"],
    "organization_files": ["id", "organization_id", "file_name", "data_type", "storage_path", "status"],
    "upload_batches": ["id", "organization_id", "file_id", "status"],
    "manual_extraction_items": ["id", "batch_id", "file_id", "status", "activity", "quantity", "unit"],
    "emission_factors": ["id", "activity", "unit", "co2e_per_unit", "scope", "country", "year"],
    "customer_factors": ["id", "organization_id", "status", "approved_by", "created_by"],
    "calculation_snapshots": ["id", "source_item_id", "content_hash", "co2e_multiplier", "factor_id"],
    "emissions_logs": ["id", "organization_id", "snapshot_id", "calculated_kg_co2e", "scope"],
    "issues": ["id", "item_id", "organization_id", "status", "blocking"],
    "report_versions": ["id", "organization_id", "status", "period_start", "period_end"],
    "conversations": ["id", "organization_id", "created_by", "title"],
    "conversation_participants": ["conversation_id", "user_id"],
    "messages": ["id", "conversation_id", "sender_id", "body", "created_at"],
    "notifications": ["id", "recipient_id", "recipient_type", "body", "read_at"],
    "facilities": ["id", "organization_id", "name", "postcode", "eircode", "is_active"],
    "assets": ["id", "organization_id", "facility_id", "name", "type"],
    "suppliers": ["id", "organization_id", "name"],
    "vehicles": ["id", "organization_id", "registration", "vehicle_type"],
    "processing_queue": ["id", "item_id", "stage", "status", "assigned_to", "entity_id"],
}


@dataclass
class TableInfo:
    name: str
    columns: List[str] = field(default_factory=list)
    column_types: Dict[str, str] = field(default_factory=dict)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    check_constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    rls_enabled: bool = False
    rls_forced: bool = False
    row_count: int = -1


class SchemaProbe:
    """Executes read-only information_schema queries against Postgres.

    If a probe dependency (psycopg/sqlalchemy) or connection is unavailable,
    callers raise :class:`~qa_harness.core.status.ToolUnavailable`.
    """

    # Read-only queries — SELECT only.
    Q_TABLES = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' ORDER BY table_name;
    """
    Q_COLUMNS = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    Q_PK = """
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.ordinal_position;
    """
    Q_FK = """
        SELECT tc.table_name, kcu.column_name, ccu.table_name AS ref_table
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
    """
    Q_UNIQUE = """
        SELECT tc.table_name, tc.constraint_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'UNIQUE' AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position;
    """
    Q_CHECKS = """
        SELECT tc.table_name, pg_get_constraintdef(c.oid) AS definition
        FROM pg_constraint c
        JOIN information_schema.table_constraints tc
          ON tc.constraint_name = c.conname
         AND tc.constraint_schema = 'public'
        WHERE c.contype = 'c' AND tc.constraint_type = 'CHECK'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name;
    """
    Q_INDEXES = """
        SELECT tablename, indexname FROM pg_indexes
        WHERE schemaname = 'public' ORDER BY tablename, indexname;
    """
    Q_TRIGGERS = """
        SELECT event_object_table, trigger_name FROM information_schema.triggers
        WHERE trigger_schema = 'public' ORDER BY event_object_table, trigger_name;
    """
    Q_RLS = """
        SELECT relname, relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relname IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
          AND relkind = 'r'
        ORDER BY relname;
    """
    Q_POLICIES = """
        SELECT schemaname, tablename, policyname, cmd, roles
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname;
    """
    Q_VIEWS = """
        SELECT table_name FROM information_schema.views
        WHERE table_schema = 'public' ORDER BY table_name;
    """
    Q_FUNCTIONS = """
        SELECT routine_name, routine_type FROM information_schema.routines
        WHERE routine_schema = 'public' ORDER BY routine_name;
    """
    Q_ROW_COUNT = "SELECT COUNT(*) AS n FROM {table};"

    def __init__(self, connection: Any) -> None:
        """``connection`` must expose a read-only cursor/execute interface."""
        self._conn = connection

    def _fetch(self, query: str, params: Optional[List[Any]] = None) -> List[tuple]:
        cursor = self._conn.cursor()
        try:
            cursor.execute(query, params or [])
            return list(cursor.fetchall())
        finally:
            cursor.close()

    def probe(self) -> Dict[str, TableInfo]:
        """Full inventory pass. Read-only by construction."""
        tables = {row[0]: TableInfo(name=row[0]) for row in self._fetch(self.Q_TABLES)}
        for table, column, data_type in self._fetch(self.Q_COLUMNS):
            if table in tables:
                tables[table].columns.append(column)
                tables[table].column_types[column] = data_type
        for table, column in self._fetch(self.Q_PK):
            if table in tables:
                tables[table].primary_key.append(column)
        for table, column, ref_table in self._fetch(self.Q_FK):
            if table in tables:
                tables[table].foreign_keys.append({"column": column, "references": ref_table})
        # Composite UNIQUE constraints arrive as one row per column; group by
        # (table, constraint_name) so a multi-column unique is one entry.
        uniques: Dict[tuple, List[str]] = {}
        for table, constraint_name, column in self._fetch(self.Q_UNIQUE):
            if table in tables:
                uniques.setdefault((table, constraint_name), []).append(column)
        for (table, _constraint_name), columns in uniques.items():
            tables[table].unique_constraints.append(columns)
        for table, constraint in self._fetch(self.Q_CHECKS):
            if table in tables:
                tables[table].check_constraints.append(constraint)
        for table, index in self._fetch(self.Q_INDEXES):
            if table in tables:
                tables[table].indexes.append(index)
        for table, trigger in self._fetch(self.Q_TRIGGERS):
            if table in tables:
                tables[table].triggers.append(trigger)
        for table, enabled, forced in self._fetch(self.Q_RLS):
            if table in tables:
                tables[table].rls_enabled = bool(enabled)
                tables[table].rls_forced = bool(forced)
        return tables


class SchemaInventory:
    """Compares a probe result against the documented expected inventory."""

    def __init__(self, expected_tables: Optional[List[str]] = None,
                 key_columns: Optional[Dict[str, List[str]]] = None) -> None:
        self.expected_tables = expected_tables or EXPECTED_TABLES
        self.key_columns = key_columns or KEY_TABLE_COLUMNS

    def missing_tables(self, probed: Dict[str, TableInfo]) -> List[str]:
        return [t for t in self.expected_tables if t not in probed]

    def missing_columns(self, probed: Dict[str, TableInfo]) -> Dict[str, List[str]]:
        missing: Dict[str, List[str]] = {}
        for table, columns in self.key_columns.items():
            info = probed.get(table)
            if info is None:
                continue
            absent = [c for c in columns if c not in info.columns]
            if absent:
                missing[table] = absent
        return missing

    def tables_without_rls(self, probed: Dict[str, TableInfo]) -> List[str]:
        return [
            name for name, info in probed.items()
            if info.row_count != 0 and not info.rls_enabled
            and name in self.expected_tables
        ]
