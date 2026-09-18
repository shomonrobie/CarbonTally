"""F-048-2/051 — activity-clarification repository: persistence + anti-bypass.

No database is touched: a scripted fake connection captures the SQL and its
parameters. The real engine functions are used (they are pure), so these tests
exercise the genuine policy re-entry rather than a stand-in.

Covered here:
* factor metadata is copied from the engine's ``ClarificationRecord`` alone;
* **no method accepts factor metadata**, so no caller — and therefore no API
  client — can nominate a factor through the repository;
* the insert is ``ON CONFLICT ... DO NOTHING`` on the database's unique key and
  a repeat returns the row already stored (idempotency), never a second row;
* every read/write is constrained by ``organization_id``;
* the decline path stores ``unresolved_declined`` with no factor;
* ``save()`` is refused so the engine remains the only author.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from data.activity_clarifications import ActivityClarificationsRepository

ORG = "11111111-1111-4111-8111-111111111111"
ITEM = "22222222-2222-4222-8222-222222222222"
ACTOR = "33333333-3333-4333-8333-333333333333"


class _FakeConn:
    def __init__(self, rows: list[Any] | None = None) -> None:
        self.rows = list(rows or [])
        self.queries: list[str] = []
        self.params: list[tuple] = []

    def _next(self) -> Any:
        return self.rows.pop(0) if self.rows else None

    async def fetchrow(self, query: str, *args: Any) -> Any:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return self._next()

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        row = self._next()
        return [] if row is None else list(row)

    async def execute(self, query: str, *args: Any) -> str:
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return "DELETE 1"


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


def _repo(rows: list[Any] | None = None):
    conn = _FakeConn(rows)
    return conn, ActivityClarificationsRepository(_FakePool(conn))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_decline_persists_no_factor_and_is_unresolved() -> None:
    conn, repo = _repo(rows=[{"id": "row-1", "outcome_status": "unresolved_declined"}])
    out = await repo.apply_decline(
        "Waste", organization_id=ORG, actor_id=ACTOR, activity_key="k1", item_id=ITEM
    )
    assert out["resolved"] is False
    params = conn.params[0]
    assert params[params.index("unresolved_declined") + 1] is None  # selected_factor_id
    assert "declined" in params  # clarification_type
    assert ACTOR in params  # actor attribution is server-supplied


@pytest.mark.asyncio
async def test_insert_is_idempotent_and_returns_the_stored_row() -> None:
    existing = {"id": "row-existing", "outcome_status": "selected"}
    conn, repo = _repo(rows=[None, existing])  # insert conflicts → re-read the stored row
    out = await repo.apply_decline("Waste", organization_id=ORG, actor_id=ACTOR, activity_key="k1")
    assert out["record"] == existing
    assert "ON CONFLICT ON CONSTRAINT activity_clarifications_unique DO NOTHING" in conn.queries[0]
    assert "activity_key = $2" in conn.queries[1]


@pytest.mark.asyncio
async def test_organization_id_is_mandatory_for_a_write() -> None:
    _conn, repo = _repo()
    from engines.activity_clarification import decline_clarification

    with pytest.raises(ValueError):
        await repo.record(decline_clarification("Waste"), organization_id="")


@pytest.mark.asyncio
async def test_reads_and_deletes_are_tenant_scoped() -> None:
    conn, repo = _repo(rows=[{"id": "r"}, None, []])
    await repo.get("row-1", organization_id=ORG)
    await repo.delete("row-1", organization_id=ORG)
    await repo.list_for_organization(ORG)
    for query in conn.queries:
        assert "organization_id = $1" in query
        assert "WHERE" in query.upper()


@pytest.mark.asyncio
async def test_resolve_context_is_server_side_and_unknown_item_is_none() -> None:
    conn, repo = _repo(rows=[{"item_key": ITEM, "batch_key": None, "organization_id": ORG}])
    ctx = await repo.resolve_context(ITEM)
    assert ctx["organization_id"] == ORG and ctx["item_key"] == ITEM
    assert "manual_extraction_batches" in conn.queries[0]
    _conn2, repo2 = _repo(rows=[None])
    assert await repo2.resolve_context(ITEM) is None


@pytest.mark.asyncio
async def test_retrieval_uses_the_database_unique_key() -> None:
    conn, repo = _repo(rows=[{"id": "r"}])
    await repo.get_adjudication("k1", "Waste", "Landfill", organization_id=ORG)
    query = conn.queries[0]
    assert "original_activity = $3" in query and "clarification = $4" in query


@pytest.mark.asyncio
async def test_save_is_refused_so_the_engine_stays_the_only_author() -> None:
    _conn, repo = _repo()
    with pytest.raises(ValueError):
        await repo.save({"id": "anything"})


def test_no_authoring_method_accepts_factor_metadata() -> None:
    """Anti-bypass by construction: there is no parameter through which to forge a factor."""
    forbidden = {
        "selected_factor_id",
        "selected_factor_name",
        "factor_set",
        "factor_source",
        "reporting_year",
        "outcome_status",
    }
    for name in ("record", "apply_clarification", "apply_decline"):
        params = set(inspect.signature(getattr(ActivityClarificationsRepository, name)).parameters)
        assert not (params & forbidden), f"{name} exposes {params & forbidden}"
