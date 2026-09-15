"""P2 EF-E — the repository's unit-selection clause (T2 semantics).

Verifies the exact SQL that ``EmissionFactorsRepository.find_by_activity`` builds,
without touching a database: a fake connection captures the query and parameters.

Covers the contract's C1/C3/C5: the strict clause only when requested, the default
(exact) and D23 (substring) modes unchanged, ``unit=None`` producing no unit clause
at all, and exact-match ranking still first.
"""

from __future__ import annotations

from typing import Any

import pytest

from data.emission_factors import EmissionFactorsRepository


class _FakeConn:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.params: list[tuple] = []

    async def fetch(self, query: str, *args: Any) -> list[dict]:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return []

    async def execute(self, query: str, *args: Any) -> str:  # pragma: no cover
        return "OK"


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


@pytest.fixture
def captured() -> tuple[_FakeConn, EmissionFactorsRepository]:
    conn = _FakeConn()
    return conn, EmissionFactorsRepository(_FakePool(conn))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_default_mode_is_exact_equality(captured) -> None:
    conn, repo = captured
    await repo.find_by_activity("gas", unit="kWh")
    sql = conn.queries[-1]
    assert "ef.unit = $2" in sql
    # no *unit-pattern* clause in default mode (the activity clause's ILIKE is unrelated)
    assert "ILIKE '%' || $2" not in sql
    assert "lower(ef.unit) LIKE" not in sql
    assert conn.params[-1][1] == "kWh"


@pytest.mark.asyncio
async def test_strict_qualifier_mode_adds_the_qualified_variant(captured) -> None:
    conn, repo = captured
    await repo.find_by_activity("gas", unit="kWh", unit_qualifier_tolerant=True)
    sql = conn.queries[-1]
    # exact OR qualified variant, and NO leading-wildcard substring pattern.
    assert "lower(ef.unit) = lower($2)" in sql
    assert "lower(ef.unit) LIKE lower($2) || ' (%'" in sql
    assert "'%' || $2 || '%'" not in sql
    # The parameter is still the normalised unit.
    assert conn.params[-1][1] == "kWh"


@pytest.mark.asyncio
async def test_alias_normalisation_still_applies_in_strict_mode(captured) -> None:
    conn, repo = captured
    await repo.find_by_activity("heating", unit="L", unit_qualifier_tolerant=True)
    assert conn.params[-1][1] == "litres"


@pytest.mark.asyncio
async def test_d23_substring_mode_is_unchanged(captured) -> None:
    conn, repo = captured
    await repo.find_by_activity("gas", unit="kWh", unit_substring=True)
    sql = conn.queries[-1]
    assert "ef.unit ILIKE '%' || $2 || '%'" in sql
    assert "lower(ef.unit) LIKE" not in sql


@pytest.mark.asyncio
async def test_strict_mode_wins_when_both_are_requested(captured) -> None:
    conn, repo = captured
    await repo.find_by_activity(
        "gas", unit="kWh", unit_substring=True, unit_qualifier_tolerant=True
    )
    sql = conn.queries[-1]
    assert "lower(ef.unit) LIKE lower($2) || ' (%'" in sql
    assert "ILIKE '%' || $2 || '%'" not in sql


@pytest.mark.asyncio
async def test_no_unit_means_no_unit_clause(captured) -> None:
    """``unit=None`` retains existing behaviour (no filter at all)."""
    conn, repo = captured
    await repo.find_by_activity("gas")
    sql = conn.queries[-1]
    assert "ef.unit" not in sql.split("ORDER BY")[0].replace("ef.unit,", "")
    assert "ORDER BY 1=1" in sql


@pytest.mark.asyncio
async def test_exact_matches_still_rank_first(captured) -> None:
    for kwargs in ({}, {"unit_substring": True}, {"unit_qualifier_tolerant": True}):
        conn = _FakeConn()
        repo = EmissionFactorsRepository(_FakePool(conn))  # type: ignore[arg-type]
        await repo.find_by_activity("gas", unit="kWh", **kwargs)
        assert "(ef.unit = $2) DESC" in conn.queries[-1]
