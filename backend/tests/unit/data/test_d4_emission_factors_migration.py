"""Phase 8 D-4 — `emission_factors` containment migration (structural tests).

Statically verifies the ratified D-4 decision (P8-FINALIZATION-IMPLEMENT-001):
`emission_factors` is internal/server-side data, so the migration must be a
REVOKE-only containment of the `anon` and `authenticated` client roles, must not
create/drop policies, must not change RLS flags, must not grant anything, and
must not touch any other table. Runtime privilege behaviour is described as
explicit verification queries in the migration footer and is exercised by the
independent post-migration census (D-14/D-15 evidence), not by this unit test.
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATION = "20260926000000_p8_d4_emission_factors_internal_containment.sql"
RLS_4A_1 = "20260920000000_p8_rls_anon_grant_containment.sql"
RLS_4B = "20260925000000_p8_rls_4b_group1_enablement.sql"


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


def _read(name: str) -> str:
    return (_repo_root() / "supabase" / "migrations" / name).read_text(encoding="utf-8")


def _executable(sql: str) -> str:
    """SQL minus comment lines (guards must not match prose about the ruling)."""
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


class TestD4MigrationShape:
    def test_migration_exists_and_sorts_after_rls_4b(self) -> None:
        migrations_dir = _repo_root() / "supabase" / "migrations"
        names = sorted(p.name for p in migrations_dir.glob("*.sql"))
        assert MIGRATION in names
        assert names.index(MIGRATION) > names.index(RLS_4B)
        assert names.index(MIGRATION) > names.index(RLS_4A_1)

    def test_revokes_both_client_roles_on_emission_factors_only(self) -> None:
        sql = _executable(_read(MIGRATION))
        assert "REVOKE ALL ON TABLE public.emission_factors FROM anon" in sql
        assert "REVOKE ALL ON TABLE public.emission_factors FROM authenticated" in sql
        revoked = re.findall(r"REVOKE\s+ALL\s+ON\s+TABLE\s+([a-zA-Z0-9_.]+)", sql)
        assert revoked, "expected explicit REVOKE statements"
        assert set(revoked) == {"public.emission_factors"} or all(
            "emission_factors" in r for r in revoked
        )

    def test_is_revoke_only(self) -> None:
        sql = _executable(_read(MIGRATION)).upper()
        assert "GRANT " not in sql
        assert "CREATE POLICY" not in sql
        assert "DROP POLICY" not in sql
        assert "ALTER POLICY" not in sql
        assert "ENABLE ROW LEVEL SECURITY" not in sql
        assert "DISABLE ROW LEVEL SECURITY" not in sql
        assert "FORCE ROW LEVEL SECURITY" not in sql
        assert "ALTER DEFAULT PRIVILEGES" not in sql

    def test_does_not_touch_service_role_or_data(self) -> None:
        sql = _executable(_read(MIGRATION))
        assert "FROM service_role" not in sql
        upper = sql.upper()
        for forbidden in ("INSERT INTO", "UPDATE ", "DELETE FROM", "TRUNCATE TABLE", "DROP TABLE"):
            assert forbidden not in upper, f"unexpected data/DDL statement: {forbidden}"

    def test_fails_closed_when_grants_remain(self) -> None:
        sql = _executable(_read(MIGRATION))
        assert "D-4 containment failed" in sql
        assert "IF after_anon <> 0 OR after_auth <> 0 THEN" in sql

    def test_documents_the_ratified_decision_and_evidence(self) -> None:
        sql = _read(MIGRATION)
        assert "D-4" in sql
        assert "internal/server-side" in sql
        assert "service_role" in sql
        assert "D-17" in sql  # production remains a terminal authorization gate
