"""I2 — bounded I1 hardening contracts (OHD F-02 / F-03 / F-04) + migration scope.

Authorization: `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (bounded I1 hardening
+ I2 only). Baseline: OHD I1 verification `66adfb5` (verdict PASS).

Asserts the three hardening dispositions that are expressible as deterministic
contracts, and that the I2 migration does exactly one thing (author-kind
integrity) with no scope leakage:

* **F-02** — ``InsightRepository.save()`` casts every parameter explicitly, so
  ``coalesce`` can no longer resolve untyped parameters to ``text`` and fail
  with ``DatatypeMismatchError`` against a ``timestamptz`` column;
* **F-03** — the authenticated insert policy on Insight messages requires
  ``role = 'user'`` (a client cannot forge the reserved author kind);
* **F-04** — ``InsightRepository.get()`` is organisation-scoped: no unscoped
  conversation read exists (``organization_id`` is a required keyword argument);
* **F-05** — the service-role grant posture is untouched by the I2 migration
  (``service_role`` keeps its platform-wide RLS bypass; application-layer
  scoping remains the boundary, recorded as a binding I3 invariant).
"""
from __future__ import annotations

import inspect
import pathlib
import re

from data.insight import InsightRepository

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATIONS = _REPO_ROOT / "supabase" / "migrations"
_I1_MIGRATION = _MIGRATIONS / "20261001000000_p8_i1_insight_persistence.sql"
_I2_MIGRATION = _MIGRATIONS / "20261002000000_p8_i2_insight_authorization.sql"
_REPOSITORY = _REPO_ROOT / "backend" / "data" / "insight.py"


def _read(path: pathlib.Path) -> str:
    assert path.exists(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


def _ddl(sql: str) -> str:
    """SQL without comment lines."""
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


# --------------------------------------------------------------------------
# F-02 — typed parameters
# --------------------------------------------------------------------------
def test_save_statement_casts_every_parameter_explicitly() -> None:
    sql = _read(_REPOSITORY)
    for cast in (
        "$1::uuid",
        "$2::uuid",
        "$3::uuid",
        "$4::text",
        "coalesce($5::timestamptz, $6::timestamptz)",
        "coalesce($7::timestamptz, $6::timestamptz)",
    ):
        assert cast in sql, cast
    # The untyped form that produced DatatypeMismatchError must be gone from the
    # statement itself (the method docstring records the defect by name).
    assert not re.search(r"VALUES\s*\([^)]*coalesce\(\$5, \$6\)", sql, re.DOTALL)
    assert not re.search(r"VALUES\s*\([^)]*coalesce\(\$7, \$6\)", sql, re.DOTALL)


# --------------------------------------------------------------------------
# F-03 — author-kind integrity in the database boundary
# --------------------------------------------------------------------------
def test_i2_migration_is_the_latest_and_scoped_to_one_policy() -> None:
    names = sorted(p.name for p in _MIGRATIONS.glob("*.sql"))
    # The P2 Insight temporal-comparison catalogue migration (PO authorization
    # 2026-09-22) is the latest; I2 remains the latest *authorization* migration,
    # unchanged in scope.
    assert names[-1] == "20261006000000_p8_insight_temporal_comparison.sql", names[-3:]
    assert _I2_MIGRATION.name in names

    ddl = _ddl(_read(_I2_MIGRATION))
    assert ddl.count("CREATE POLICY") == 1
    assert ddl.count("DROP POLICY") == 1
    # Minimum change: no table/column/index/grant/RLS-state change, and no other
    # Insight table touched.
    for forbidden in (
        "CREATE TABLE",
        "ALTER TABLE",
        "CREATE INDEX",
        "GRANT",
        "REVOKE",
    ):
        assert forbidden not in ddl, forbidden


def test_i2_insert_policy_pins_the_author_kind_to_human_messages() -> None:
    ddl = _ddl(_read(_I2_MIGRATION))
    policy = ddl[ddl.index("CREATE POLICY") :]
    assert "ci_messages_conversation_creator_insert" in policy
    assert "FOR INSERT TO authenticated" in policy
    # Organisation scope + creator identity (I1) preserved, plus the new rule.
    assert "public.is_org_member(organization_id)" in policy
    assert "created_by = auth.uid()" in policy
    assert "c.created_by = auth.uid()" in policy
    assert "role = 'user'" in policy
    # Idempotent, re-runnable guard.
    assert "FROM pg_policies" in ddl
    assert "IF EXISTS" in ddl


def test_i2_migration_does_not_touch_messaging_or_dormant_ai_structures() -> None:
    ddl = _ddl(_read(_I2_MIGRATION))
    for table in (
        "public.conversations",
        "public.messages",
        "public.message_activity_log",
        "ai_content_history",
    ):
        assert table not in ddl, table
    assert "audit" not in ddl.lower()


def test_f05_service_role_posture_is_unchanged_by_i2() -> None:
    """service_role keeps its platform-wide RLS bypass (not modified by I2)."""
    i1 = _ddl(_read(_I1_MIGRATION))
    assert "GRANT ALL ON TABLE public.carbontally_insight_messages      TO service_role" in i1
    i2 = _ddl(_read(_I2_MIGRATION))
    assert "service_role" not in i2


# --------------------------------------------------------------------------
# F-04 — no unscoped conversation read
# --------------------------------------------------------------------------
def test_get_requires_an_organization_scope() -> None:
    signature = inspect.signature(InsightRepository.get)
    scope = signature.parameters["organization_id"]
    assert scope.kind is inspect.Parameter.KEYWORD_ONLY
    assert scope.default is inspect.Parameter.empty, "organization_id must be required"


def test_repository_has_no_unscoped_conversation_read() -> None:
    sql = _read(_REPOSITORY)
    unscoped = re.findall(
        r"FROM public\.carbontally_insight_conversations\s+WHERE id = \$1(?!\s*AND organization_id)",
        sql,
    )
    assert unscoped == [], "an unscoped conversation read exists"
    assert "WHERE id = $1 AND organization_id = $2" in sql
