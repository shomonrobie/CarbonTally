"""CT-FINAL-01 / PD-4 — legacy audit console retirement guard.

PD-4 (ratified production scope) formally retires the orphan legacy admin audit
console ``backend/routes/admin/audit_logs.py`` — 12 endpoints that were never
imported, never registered and never startup-checked, one of which queried the
non-existent ``notification_delivery_log`` table
(CT-SCHEMA-03 SCM-007, CT-AUDIT-01 §1.1 / PD-7.1 option (ii)).

These tests lock the retirement and the "historical records preserved" promise:

* the retired module is gone and nothing in ``backend/`` imports or registers it;
* nothing in runtime code references the retired table name
  ``notification_delivery_log``;
* the canonical audit implementation it was superseded by still exists
  (``audit_trail`` ledger + the registered read surfaces);
* the legacy audit/history tables are still defined by the migration chain and
  their immutability migration is intact — the retirement removed *code*, never
  *records*.
"""
from __future__ import annotations

from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3]
_REPO_ROOT = _BACKEND.parent

#: The artefact retired by PD-4.
RETIRED_MODULE = _BACKEND / "routes" / "admin" / "audit_logs.py"

#: The canonical audit ledger and the module that writes it.
_CANONICAL_LEDGER = "audit_trail"
_CANONICAL_WRITER_RELATIVE_PATH = "backend/data/audit.py"

#: Registered canonical audit read surfaces (a sample replacement set).
_CANONICAL_SURFACES = (
    ("backend/api/v3_reporting.py", "/api/v3/ops/reporting/audit"),
    ("backend/api/admin_audit.py", '/api/v2/admin/audit'),
)

#: The DB-0001 migration that makes the legacy audit/activity tables immutable.
#: It must never be removed by this change: PD-4 retired code, not guarantees.
_IMMUTABILITY_MIGRATION = (
    _REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260831020000_audit_activity_immutability.sql"
)

#: The Phase-7 migration that documents the canonical ledger and the legacy
#: tables as *retained* (append-only).
_CANONICAL_LEDGER_MIGRATION = (
    _REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260912000000_p7_audit_immutability_and_indexes.sql"
)

#: Legacy per-domain activity tables that PD-4 explicitly does NOT drop.
_LEGACY_TABLES_PRESERVED = ("audit_logs", "activity_logs", "document_activity_log")


def _runtime_modules() -> list[Path]:
    """Every non-test Python module shipped under ``backend/``."""
    return [
        path
        for path in _BACKEND.rglob("*.py")
        if ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and "tests" not in path.parts
    ]


def test_retired_legacy_audit_console_is_gone() -> None:
    assert not RETIRED_MODULE.exists(), (
        "PD-4 retired backend/routes/admin/audit_logs.py; it must not return"
    )


def test_no_runtime_module_imports_the_retired_console() -> None:
    offenders: list[str] = []
    for path in _runtime_modules():
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in ("routes.admin.audit_logs", "admin.audit_logs", "import audit_logs"):
            if needle in text:
                offenders.append(f"{path.relative_to(_BACKEND)}: {needle}")
    assert offenders == [], "retired audit console still referenced: " + "; ".join(offenders)


def test_no_runtime_module_references_the_nonexistent_delivery_log_table() -> None:
    """``notification_delivery_log`` does not exist; the canonical table is
    ``notification_delivery`` (CT-AUDIT-01 §1.1)."""
    offenders: list[str] = []
    for path in _runtime_modules():
        text = path.read_text(encoding="utf-8", errors="replace")
        if "notification_delivery_log" in text:
            offenders.append(str(path.relative_to(_BACKEND)))
    assert offenders == [], (
        "a non-existent table is still referenced: " + "; ".join(offenders)
    )


def test_canonical_audit_ledger_and_writer_still_exist() -> None:
    writer = _REPO_ROOT / _CANONICAL_WRITER_RELATIVE_PATH
    assert writer.exists(), "the canonical audit repository must still exist"
    assert _CANONICAL_LEDGER in writer.read_text(encoding="utf-8")


def test_canonical_audit_read_surfaces_remain_registered() -> None:
    missing: list[str] = []
    for relative_path, route in _CANONICAL_SURFACES:
        path = _REPO_ROOT / relative_path
        if not path.exists() or route not in path.read_text(encoding="utf-8"):
            missing.append(f"{relative_path}: {route}")
    assert missing == [], "canonical audit surface missing: " + "; ".join(missing)


def test_legacy_audit_tables_are_preserved_by_the_migration_chain() -> None:
    """PD-4 removed code, never records: the tables and their immutability stay."""
    migration = _IMMUTABILITY_MIGRATION.read_text(encoding="utf-8").lower()
    normalised = " ".join(migration.split())
    for table in _LEGACY_TABLES_PRESERVED:
        assert f"drop policy if exists {table}_tenant_delete" in normalised
        assert f"drop policy if exists {table}_tenant_update" in normalised
    # No table is dropped at all by the immutability migration.
    assert "drop table" not in normalised


def test_canonical_audit_ledger_migration_is_intact() -> None:
    text = _CANONICAL_LEDGER_MIGRATION.read_text(encoding="utf-8")
    assert _CANONICAL_LEDGER in text
    for table in _LEGACY_TABLES_PRESERVED:
        assert table in text, f"{table} must remain documented as retained"
