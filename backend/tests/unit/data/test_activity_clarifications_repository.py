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
from engines.activity_clarification import ClarificationRecord

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
    assert (
        "ON CONFLICT ON CONSTRAINT activity_clarifications_replay_unique DO NOTHING"
        in conn.queries[0]
    )
    assert "activity_key = $2" in conn.queries[1]
    assert "AND version = $5" in conn.queries[1]


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


# ---------------------------------------------------------------------------
# Adjudication lifecycle (F-039-1 A/B/C/D) — versioned, context-bounded
# ---------------------------------------------------------------------------

CURRENT_V1 = {
    "id": "row-v1",
    "adjudication_id": "adj-1",
    "version": 1,
    "clarification": "Landfill",
    "is_current": True,
    "factor_set": "DEFRA-2025",
}


def _landfill_record(*, clarification: str = "Landfill") -> ClarificationRecord:
    """An engine-shaped adjudication record (the repository persists these only)."""
    return ClarificationRecord(
        clarification_id="c1",
        activity_key="k1",
        original_activity="Waste",
        clarification=clarification,
        clarification_type="semantic_activity",
        status="clarification_supplied",
        outcome_status="selected",
        policy_input=f"Waste {clarification}",
        actor_id=ACTOR,
        actor_scope="organization_member",
        created_at="2026-09-18T00:00:00+00:00",
    )


@pytest.mark.asyncio
async def test_effective_lookup_requires_the_full_context_boundary() -> None:
    conn, repo = _repo(rows=[CURRENT_V1])
    row = await repo.effective(
        organization_id=ORG, activity_key="k1", original_activity="Waste"
    )
    assert row == CURRENT_V1
    query = conn.queries[0]
    assert "is_current" in query
    assert "effective_context_key = $2" in query
    assert "original_activity = $4" in query  # never activity text alone


@pytest.mark.asyncio
async def test_modification_creates_a_new_version_and_retires_the_previous() -> None:
    conn, repo = _repo(
        rows=[
            CURRENT_V1,  # effective lookup → existing version 1
            {"id": "row-v2", "version": 2, "supersedes_id": "row-v1"},  # inserted v2
            "UPDATE 1",  # supersede
        ]
    )
    stored = await repo.apply_versioned(
        _landfill_record(clarification="Incineration"),
        organization_id=ORG,
        actor_id=ACTOR,
    )
    assert stored["version"] == 2
    # version 2 insert carries adjudication identity, version and supersedes linkage
    insert = conn.params[1]
    assert "adj-1" in insert  # same adjudication_id as version 1
    assert 2 in insert  # version
    assert "row-v1" in insert  # supersedes_id
    # the ONLY statement touching the old version is the is_current flip
    update_sql = conn.queries[2]
    assert update_sql.startswith("UPDATE public.activity_clarifications")
    # only the currency flag changes — no clarification/outcome/factor column is touched
    assignments = update_sql.split("SET", 1)[1].split("WHERE")[0]
    assert assignments.strip().startswith("is_current = false")
    assert "selected_factor" not in assignments
    assert "outcome_status" not in assignments


@pytest.mark.asyncio
async def test_identical_clarification_is_a_replay_not_a_new_version() -> None:
    conn, repo = _repo(rows=[CURRENT_V1])
    stored = await repo.apply_versioned(
        _landfill_record(clarification="Landfill"),
        organization_id=ORG,
        actor_id=ACTOR,
    )
    assert stored == CURRENT_V1
    assert len(conn.queries) == 1  # no insert, no supersede


@pytest.mark.asyncio
async def test_history_is_deterministic_oldest_first_and_tenant_scoped() -> None:
    conn, repo = _repo(rows=[[{"version": 1}, {"version": 2}]])
    rows = await repo.history("adj-1", organization_id=ORG)
    assert [r["version"] for r in rows] == [1, 2]
    query = conn.queries[0]
    assert "ORDER BY version ASC" in query
    assert "organization_id = $1" in query


# ---------------------------------------------------------------------------
# Evidence provenance + D-F039-1-I compatibility signature
# ---------------------------------------------------------------------------


def test_signature_covers_exactly_activity_unit_and_scope() -> None:
    base = ActivityClarificationsRepository.evidence_signature("Waste", "tonnes", "Scope 3")
    assert base == ActivityClarificationsRepository.evidence_signature(
        " waste ", "TONNES", "scope 3"
    )  # normalised
    assert base != ActivityClarificationsRepository.evidence_signature(
        "Waste", "litres", "Scope 3"
    )
    assert base != ActivityClarificationsRepository.evidence_signature(
        "Waste", "tonnes", "Scope 1"
    )
    assert base != ActivityClarificationsRepository.evidence_signature(
        "Waste disposal", "tonnes", "Scope 3"
    )


@pytest.mark.asyncio
async def test_resolve_evidence_derives_provenance_and_authoritative_unit() -> None:
    conn, repo = _repo(
        rows=[
            {
                "item_key": ITEM,
                "batch_key": None,
                "organization_id": ORG,
                "source_file_id": "file-9",
                "source_file_name": "invoice.pdf",
                "extracted_data": {
                    "line_items": [
                        {"activity": "Waste", "unit": "tonnes", "scope": "Scope 3"},
                        {"activity": "Diesel", "unit": "litres"},
                    ]
                },
            }
        ]
    )
    ctx = await repo.resolve_evidence(ITEM, "Waste")
    assert ctx["organization_id"] == ORG
    assert ctx["source_evidence_ref"] == "file-9"  # persisted file identity, not the body
    assert ctx["unit"] == "tonnes" and ctx["scope"] == "Scope 3"


@pytest.mark.asyncio
async def test_unmatched_or_ambiguous_line_yields_no_unit_and_no_invention() -> None:
    conn, repo = _repo(
        rows=[
            {
                "item_key": ITEM,
                "organization_id": ORG,
                "extracted_data": {
                    "line_items": [
                        {"activity": "Waste", "unit": "tonnes"},
                        {"source_line": "Waste", "unit": "litres"},
                    ]
                },
            }
        ]
    )
    ctx = await repo.resolve_evidence(ITEM, "Waste")  # two matching lines
    assert ctx["unit"] is None and ctx["scope"] is None
    conn2, repo2 = _repo(rows=[{"item_key": ITEM, "organization_id": ORG, "extracted_data": None}])
    ctx2 = await repo2.resolve_evidence(ITEM, "Waste")
    assert ctx2["unit"] is None and ctx2["scope"] is None


@pytest.mark.asyncio
async def test_effective_compatible_requires_a_matching_evidence_signature() -> None:
    sig = ActivityClarificationsRepository.evidence_signature("Waste", "tonnes", "Scope 3")
    row = dict(CURRENT_V1, evidence_signature=sig)
    conn, repo = _repo(rows=[row])
    got, ok = await repo.effective_compatible(
        organization_id=ORG,
        activity_key="k1",
        original_activity="Waste",
        unit="tonnes",
        scope="Scope 3",
    )
    assert ok is True and got == row


@pytest.mark.asyncio
async def test_effective_compatible_rejects_changed_evidence_and_missing_signature() -> None:
    sig = ActivityClarificationsRepository.evidence_signature("Waste", "tonnes", "Scope 3")
    changed = dict(CURRENT_V1, evidence_signature=sig)
    _c, repo = _repo(rows=[changed])
    got, ok = await repo.effective_compatible(
        organization_id=ORG,
        activity_key="k1",
        original_activity="Waste",
        unit="litres",  # evidence changed
        scope="Scope 3",
    )
    assert got is not None and ok is False

    legacy = dict(CURRENT_V1, evidence_signature=None)
    _c2, repo2 = _repo(rows=[legacy])
    got2, ok2 = await repo2.effective_compatible(
        organization_id=ORG,
        activity_key="k1",
        original_activity="Waste",
        unit="tonnes",
        scope="Scope 3",
    )
    assert got2 is not None and ok2 is False  # no proof of compatibility → not reused

    _c3, repo3 = _repo(rows=[None])
    got3, ok3 = await repo3.effective_compatible(
        organization_id=ORG,
        activity_key="k1",
        original_activity="Waste",
        unit=None,
        scope=None,
    )
    assert got3 is None and ok3 is False
