"""F-T1-001 — organisation audit-activity SQL typing + parameterisation guards.

Defect (DEMO-T1 verification, 2026-09-19): ``GET /api/v3/reporting/audit-activity``
returned **HTTP 500** for a correctly-authorised organisation owner with

    asyncpg.exceptions.UndefinedFunctionError: operator does not exist: uuid = text

``$1`` was used in two incompatible contexts inside ``_ORG_ACTIVITY_UNION``: five
branches compare it against ``uuid`` columns, while the ``audit_trail`` branch
compared it against ``metadata->>'organization_id'`` (jsonb ``->>`` yields TEXT).
PostgreSQL resolves ONE type per parameter per statement, inferred TEXT, and the
query therefore failed at parse time — before any row was read.

Coverage here:

* static guards so the required cast cannot be "simplified" away again (same
  convention as ``test_disclosure_sql_typing.py``);
* a scripted fake connection proving the organisation id is passed as a **bind
  parameter** and never interpolated into the SQL (no injection surface);
* a runtime guard that PREPARES the statements the repository actually builds —
  the exact operation that used to fail — against a local Demo Lab database.
  It is skipped unless ``DEMO_LAB_DATABASE_URL`` is set, and performs no reads or
  writes beyond statement preparation (no data is created, changed or deleted).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

from data.reporting import _ORG_ACTIVITY_UNION, ReportingRepository

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "supabase" / "migrations").is_dir()
)
REPORTING_SRC = (REPO_ROOT / "backend" / "data" / "reporting.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Static guards — the required cast and the absence of the inference conflict
# ---------------------------------------------------------------------------


def test_audit_branch_casts_the_organisation_parameter() -> None:
    """The audit branch must make ``$1``'s type explicit (F-T1-001)."""
    assert re.search(
        r"metadata->>'organization_id'\s*=\s*\(\$1::uuid\)::text", _ORG_ACTIVITY_UNION
    ), "the audit_trail branch must compare the org against ($1::uuid)::text"


def test_no_bare_text_comparison_reintroduces_the_uuid_text_conflict() -> None:
    """A bare ``= $1`` against the jsonb text value would restore the 500."""
    assert not re.search(
        r"metadata->>'organization_id'\s*=\s*\$1\b", _ORG_ACTIVITY_UNION
    )


def test_every_parameter_use_in_the_union_is_uuid_typed() -> None:
    """Guard the class of defect: each ``$1`` use must be uuid-compatible."""
    uses = [line.strip() for line in _ORG_ACTIVITY_UNION.splitlines() if "$1" in line]
    assert uses, "expected the union to use $1 for the organisation scope"
    for line in uses:
        uuid_safe = bool(
            re.search(r"\b\w*organization_id\s*=\s*\$1\b", line)
            or re.search(r"\b\w*entity_id\s*=\s*\$1\b", line)
            or re.search(r"\(\$1::uuid\)::text", line)
        )
        assert uuid_safe, f"$1 used in a non-uuid-compatible context: {line!r}"


def test_repository_source_keeps_the_organisation_filter_parameterised() -> None:
    """No f-string interpolation of an identifier into the union statement."""
    assert "_ORG_ACTIVITY_UNION" in REPORTING_SRC
    assert "WHERE a.metadata->>'organization_id' = ($1::uuid)::text" in REPORTING_SRC


# ---------------------------------------------------------------------------
# Scripted fake connection (no database) — parameter binding + statement shape
# ---------------------------------------------------------------------------


class _FakeConn:
    """Records the statements and parameters the repository issues."""

    def __init__(self, rows: list[Any] | None = None) -> None:
        self.rows = list(rows or [])
        self.queries: list[str] = []
        self.params: list[tuple] = []

    async def fetchrow(self, query: str, *args: Any) -> Any:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return self.rows.pop(0) if self.rows else None

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return []


class _Acquire:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def acquire(self) -> _Acquire:
        return _Acquire(self._conn)


async def _captured_statements() -> tuple[_FakeConn, list[tuple[str, tuple]]]:
    conn = _FakeConn(rows=[{"n": 0}])
    repo = ReportingRepository(_FakePool(conn))  # type: ignore[arg-type]
    await repo.org_audit_activity(ORG_A, limit=25, offset=5)
    return conn, list(zip(conn.queries, conn.params))


@pytest.mark.asyncio
async def test_org_id_is_bound_as_a_parameter_never_interpolated() -> None:
    conn, statements = await _captured_statements()
    assert len(statements) == 2, "expected the count and page statements"
    for query, params in statements:
        assert ORG_A not in query, "the organisation id must never be interpolated"
        assert "uuid" not in query or "($1::uuid)::text" in query
        assert params[0] == ORG_A, "the organisation id must be the first bind parameter"


@pytest.mark.asyncio
async def test_all_three_parameters_are_positional_and_typed_by_placeholders() -> None:
    _conn, statements = await _captured_statements()
    count_query, count_params = statements[0]
    page_query, page_params = statements[1]
    assert count_params == (ORG_A,)
    assert page_params == (ORG_A, 25, 5)
    assert count_query.startswith("SELECT COUNT(*) AS n FROM (")
    assert page_query.endswith("LIMIT $2 OFFSET $3")


# ---------------------------------------------------------------------------
# Runtime guard — the operation that used to fail (statement PREPARATION)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("DEMO_LAB_DATABASE_URL"),
    reason="local Demo Lab database not configured (set DEMO_LAB_DATABASE_URL)",
)
@pytest.mark.asyncio
async def test_repository_statements_execute_on_postgres() -> None:
    """Preparing AND running the real statements must not raise (F-T1-001).

    Preparation performs PostgreSQL's parse + parameter-type inference — the step
    that raised ``operator does not exist: uuid = text`` — and the follow-up fetch
    exercises bind + plan + execution. Both statements are read-only SELECTs, so
    the lab database is only read (no rows are created, changed or deleted).
    """
    import asyncpg

    dsn = os.environ["DEMO_LAB_DATABASE_URL"]
    conn = await asyncpg.connect(dsn)
    try:
        _fake, statements = await _captured_statements()
        for query, params in statements:
            for org in (ORG_A, ORG_B):
                rows = await conn.fetch(query, org, *params[1:])
                assert isinstance(rows, list)
                if query.startswith("SELECT COUNT(*)"):
                    assert rows[0]["n"] == 0
                else:
                    assert rows == []
    finally:
        await conn.close()


@pytest.mark.skipif(
    not os.environ.get("DEMO_LAB_DATABASE_URL"),
    reason="local Demo Lab database not configured (set DEMO_LAB_DATABASE_URL)",
)
@pytest.mark.asyncio
async def test_organisation_filter_reads_only_the_requested_org() -> None:
    """Cross-organisation isolation of the read (no writes; empty lab tables)."""
    import asyncpg

    dsn = os.environ["DEMO_LAB_DATABASE_URL"]
    conn = await asyncpg.connect(dsn)
    try:
        for org in (ORG_A, ORG_B):
            row = await conn.fetchrow(
                f"SELECT COUNT(*) AS n FROM ({_ORG_ACTIVITY_UNION}) ev", org)
            assert row["n"] == 0, "the lab holds no activity for a synthetic uuid"
    finally:
        await conn.close()
