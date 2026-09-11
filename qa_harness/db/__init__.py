"""Read-only database QA module.

Inspects tables, columns, types, primary/foreign/unique/check constraints,
indexes, triggers, views, functions, RLS state/policies and migration state.
Every query is read-only; the module never issues DDL/DML.
"""

from qa_harness.db.schema_inventory import SchemaInventory, SchemaProbe
from qa_harness.db.integrity import IntegrityAudit, IntegrityRule
from qa_harness.db.indexes import IndexAudit
from qa_harness.db.constraints import ConstraintAudit
from qa_harness.db.rls import RlsAudit, RlsExpectation
from qa_harness.db.migrations import MigrationAudit

__all__ = [
    "ConstraintAudit",
    "IndexAudit",
    "IntegrityAudit",
    "IntegrityRule",
    "MigrationAudit",
    "RlsAudit",
    "RlsExpectation",
    "SchemaInventory",
    "SchemaProbe",
]
