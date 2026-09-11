"""WS5 / DB-0002 — tenant organization_id NOT NULL migration regression tests.

Deterministic tests reading the migration file and verifying:

* only `assets.organization_id` is made NOT NULL (the strictly tenant-scoped
  table whose every insertion path supplies the org id),
* no other table is altered (NULL stays legitimate for system/global rows),
* the migration is non-destructive (no DROP/TRUNCATE).
"""
from __future__ import annotations

from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "supabase" / "migrations"
MIGRATION = MIGRATIONS_DIR / "20260831030000_tenant_org_id_not_null.sql"


def _read() -> str:
    assert MIGRATION.exists(), f"migration file missing: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def _normalize(sql: str) -> str:
    return " ".join(sql.split()).lower()


def test_assets_organization_id_set_not_null() -> None:
    sql = _normalize(_read())
    assert (
        "alter table public.assets alter column organization_id set not null"
        in sql
    )


def test_no_other_table_is_altered() -> None:
    sql = _read().upper()
    for table in (
        "ACTIVITY_FEED",
        "AUDIT_LOGS",
        "ACTIVITY_LOGS",
        "DOCUMENT_ACTIVITY_LOG",
        "FACTOR_ALIASES",
        "REPORT_TEMPLATES",
        "ISSUES",
        "DRAFT_ENTRIES",
        "EXPORT_HISTORY",
        "PROCESSING_LOGS",
        "USER_FEEDBACK",
        "USER_INVITATIONS",
    ):
        assert f"ALTER TABLE PUBLIC.{table}" not in sql, table


def test_non_destructive() -> None:
    sql = _read().upper()
    assert "DROP TABLE" not in sql
    assert "TRUNCATE" not in sql
    assert "DELETE FROM" not in sql
