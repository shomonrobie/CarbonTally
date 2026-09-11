"""BL-1 / BL-3 migration regression tests.

These deterministic tests read the migration files (the canonical definition
of the schema change) and verify the invariants the audit backlog required:

* BL-1 (v3m10): organisation membership uniqueness is enforced by a UNIQUE
  index on (organization_id, user_id) and the migration is idempotent.
* BL-3 (v3m11): the four operational performance indexes exist, are created
  with IF NOT EXISTS (idempotent), and reference the exact (table, column)
  predicates the RC2 schema inventory flagged as unindexed.

They run with zero external dependencies and no database connection.
"""
from __future__ import annotations

from pathlib import Path

MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[4] / "supabase" / "migrations"
)

V3M10 = MIGRATIONS_DIR / "20260831000000_v3m10_org_membership_unique.sql"
V3M11 = MIGRATIONS_DIR / "20260831010000_v3m11_operational_indexes.sql"


def _read(path: Path) -> str:
    assert path.exists(), f"migration file missing: {path}"
    return path.read_text(encoding="utf-8")


def _normalize(sql: str) -> str:
    """Collapse whitespace so statement assertions tolerate formatting."""
    return " ".join(sql.split()).lower()


def test_v3m10_enforces_membership_uniqueness() -> None:
    sql = _normalize(_read(V3M10))
    assert "create unique index if not exists organization_members_org_user_uniq" in sql
    assert "on public.organization_members (organization_id, user_id)" in sql


def test_v3m10_is_idempotent() -> None:
    sql = _read(V3M10)
    assert "IF NOT EXISTS" in sql
    assert "DROP INDEX" not in sql


def test_v3m11_creates_all_four_operational_indexes() -> None:
    sql = _normalize(_read(V3M11))
    expected = {
        "idx_upload_batches_organization_id": "on public.upload_batches (organization_id)",
        "idx_upload_batches_status": "on public.upload_batches (status)",
        "idx_manual_extraction_items_batch_id": "on public.manual_extraction_items (batch_id)",
        "idx_manual_extraction_items_status": "on public.manual_extraction_items (status)",
    }
    for name, definition in expected.items():
        assert f"create index if not exists {name}" in sql, name
        assert definition in sql, name


def test_v3m11_is_idempotent_and_non_destructive() -> None:
    sql = _read(V3M11)
    assert sql.count("CREATE INDEX IF NOT EXISTS") == 4
    assert "DROP INDEX" not in sql
    assert "DROP TABLE" not in sql
    assert "ALTER TABLE" not in sql


def test_v3m11_index_names_follow_convention() -> None:
    import re

    sql = _read(V3M11)
    # Existing canonical indexes use idx_<table>_<column>; no duplicated names.
    names = re.findall(
        r"CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.]+)",
        sql,
        flags=re.IGNORECASE,
    )
    assert len(names) == 4, f"expected 4 index statements, got {names}"
    assert len(names) == len(set(names)), f"duplicate index names: {names}"
    for name in names:
        assert name.startswith("idx_"), name
