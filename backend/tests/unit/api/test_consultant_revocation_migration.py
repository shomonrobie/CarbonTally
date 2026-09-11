"""WS6 / SEC-0003 — consultant revocation migration regression tests.

Deterministic tests reading the migration file and verifying:

* `is_consultant_firm_revoker` is role-based (owner/admin/manager),
* `cc_delete_own_firm` is scoped to the revoker helper,
* `consultant_clients_tenant_delete` is scoped to customer owner/admin
  (`is_org_admin_or_owner`) — Member/Viewer cannot sever the relationship,
* no destructive statement exists.
"""
from __future__ import annotations

from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[4] / "supabase" / "migrations"
MIGRATION = MIGRATIONS_DIR / "20260831040000_consultant_revocation_roles.sql"


def _read() -> str:
    assert MIGRATION.exists(), f"migration file missing: {MIGRATION}"
    return MIGRATION.read_text(encoding="utf-8")


def _normalize(sql: str) -> str:
    return " ".join(sql.split()).lower()


def test_revoker_helper_is_role_based() -> None:
    sql = _normalize(_read())
    assert "create or replace function public.is_consultant_firm_revoker" in sql
    assert "me.role in ('owner', 'admin', 'manager')" in sql
    assert "and coalesce(me.is_active, true) = true" in sql


def test_cc_delete_own_firm_uses_revoker() -> None:
    sql = _normalize(_read())
    assert (
        "create policy cc_delete_own_firm on public.consultant_clients "
        "for delete to authenticated using (public.is_consultant_firm_revoker(consultant_id))"
        in sql
    )


def test_tenant_delete_restricted_to_org_admin_or_owner() -> None:
    sql = _normalize(_read())
    assert (
        "create policy consultant_clients_tenant_delete on public.consultant_clients "
        "for delete to authenticated using (public.is_org_admin_or_owner(organization_id))"
        in sql
    )


def test_migration_is_non_destructive() -> None:
    sql = _read().upper()
    assert "DROP TABLE" not in sql
    assert "TRUNCATE" not in sql
    assert "DELETE FROM" not in sql
