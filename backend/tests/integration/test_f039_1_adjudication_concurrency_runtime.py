"""R67 — D-F039-1-J concurrency suite: one lineage per bounded context.

Every test below runs against a real asyncpg pool, the real repository and (for the API
case) the real router, and every race is run with an explicitly WARMED pool so no result
can depend on pool warm-up latency. The bounded context exercised is the one the shipped
code uses — ``organization_id · effective_context_key · activity_key ·
original_activity`` — with the same call shape as the API
(``context_key = activity_key = item_id``, ``original_activity`` = the extracted text).

Focused run:

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_f0391_065 \
        python -m pytest tests/integration/test_f039_1_adjudication_concurrency_runtime.py
"""
from __future__ import annotations

import asyncio
import uuid

import asyncpg
import pytest

from data.activity_clarifications import (
    ActivityClarificationsRepository,
    AdjudicationConcurrencyConflict,
)
from engines.activity_clarification import resolve_clarification
from tests.integration.test_f039_1_adjudication_lifecycle_runtime import (
    CLARIFY,
    EFFECTIVE,
    HISTORY,
    _client,
    _api_app,
    _member,
    _new_item,
    _new_org,
    _seed_factors,
)

#: Distinct semantic clarifications ⇒ each concurrent writer is a genuine modification,
#: so a correct implementation must produce contiguous versions 1..N in ONE lineage.
_DISTINCT = ("Landfill", "Incineration", "Waste oils", "Open-loop", "Composting")

#: The semantic-option discovery endpoint (the API validates submissions against it).
OPTIONS = "/api/v3/activity-clarifications/options"


async def _warm(pool, n: int) -> None:
    """Open n live connections before any race (no reliance on warm-up side effects)."""
    await asyncio.gather(*[pool.fetchval("SELECT 1") for _ in range(n)])


def _rec(key: str, clarification: str):
    rec, _factor = resolve_clarification("Waste", clarification, [], activity_key=key)
    return rec


async def _race(pool, org: str, key: str, clarifications, *, signature="sig-r067",
                **extra) -> list:
    """Run one concurrent write per clarification against the same bounded context."""
    repo = ActivityClarificationsRepository(pool)
    actor = str(uuid.uuid4())
    return await asyncio.gather(*[
        repo.apply_versioned(_rec(key, c), organization_id=org, actor_id=actor,
                             context_key=key, evidence_signature=signature, **extra)
        for c in clarifications
    ], return_exceptions=True)


async def _lineage(pool, org: str, key: str):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, adjudication_id, version, is_current, clarification "
            "FROM public.activity_clarifications "
            "WHERE organization_id=$1 AND effective_context_key=$2 "
            "ORDER BY version", org, key)
    return rows


# ---------------------------------------------------------------------------
# TEST A — concurrent FIRST writes must converge on ONE lineage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_concurrent_first_writes_converge_on_one_lineage(pool) -> None:
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    n = len(_DISTINCT)
    await _warm(pool, n)                       # explicitly warm: worst case for the race

    results = await _race(pool, org, key, _DISTINCT)

    errors = [r for r in results if isinstance(r, BaseException)]
    assert not errors, errors
    rows = await _lineage(pool, org, key)
    lineage_ids = {str(r["adjudication_id"]) for r in rows}
    assert len(lineage_ids) == 1, f"expected ONE lineage, got {lineage_ids}"
    assert [int(r["version"]) for r in rows] == [1, 2, 3, 4, 5]
    assert sum(1 for r in rows if r["is_current"]) == 1
    # every successful write belongs to that same lineage (none silently forked)
    assert {str(r["adjudication_id"]) for r in results} == lineage_ids
    assert len({str(r["id"]) for r in results}) == n     # no lost successful update


# ---------------------------------------------------------------------------
# TEST B — concurrent writes against an EXISTING lineage stay in that lineage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b_concurrent_writes_to_an_existing_lineage_stay_in_it(pool) -> None:
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    repo = ActivityClarificationsRepository(pool)
    actor = str(uuid.uuid4())

    seed = await repo.apply_versioned(
        _rec(key, "Landfill"), organization_id=org, actor_id=actor, context_key=key,
        evidence_signature="sig-r067")
    await _warm(pool, 4)

    results = await _race(pool, org, key, _DISTINCT[1:])

    assert not [r for r in results if isinstance(r, BaseException)], results
    rows = await _lineage(pool, org, key)
    assert {str(r["adjudication_id"]) for r in rows} == {str(seed["adjudication_id"])}
    assert [int(r["version"]) for r in rows] == [1, 2, 3, 4, 5]
    assert sum(1 for r in rows if r["is_current"]) == 1
    # immutable history: v1 keeps its original clarification and identity
    assert rows[0]["id"] == seed["id"]
    assert rows[0]["clarification"] == "Landfill"
    assert rows[0]["is_current"] is False
    # no lost successful adjudication update
    assert len({str(r["id"]) for r in results}) == len(_DISTINCT) - 1


# ---------------------------------------------------------------------------
# TEST C — concurrent IDENTICAL requests are idempotent in one lineage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_c_concurrent_identical_requests_are_idempotent(pool) -> None:
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    await _warm(pool, 5)

    results = await _race(pool, org, key, ["Landfill"] * 5)

    assert not [r for r in results if isinstance(r, BaseException)], results
    rows = await _lineage(pool, org, key)
    assert len(rows) == 1, f"identical concurrent writes must not version: {rows}"
    assert int(rows[0]["version"]) == 1 and rows[0]["is_current"] is True
    assert {str(r["id"]) for r in results} == {str(rows[0]["id"])}
    assert {str(r["clarification"]) for r in results} == {"Landfill"}



# ---------------------------------------------------------------------------
# TEST D — rollback/failure under contention, and the DB-level guarantee
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_d_failed_transaction_leaves_no_orphan_or_duplicate_current(pool) -> None:
    """A real DB failure AFTER the retire must roll the retire back (no orphan state)."""
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    repo = ActivityClarificationsRepository(pool)
    actor = str(uuid.uuid4())

    seed = await repo.apply_versioned(
        _rec(key, "Landfill"), organization_id=org, actor_id=actor, context_key=key,
        evidence_signature="sig-r067")

    # fault injection through a REAL constraint: an unknown batch_key violates the
    # batch FK during the insert that follows the retire.
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await repo.apply_versioned(
            _rec(key, "Incineration"), organization_id=org, actor_id=actor, context_key=key,
            evidence_signature="sig-r067", batch_key=str(uuid.uuid4()))

    rows = await _lineage(pool, org, key)
    assert len(rows) == 1                        # no orphan half-written version
    assert rows[0]["id"] == seed["id"]
    assert rows[0]["is_current"] is True         # the retire was rolled back
    assert int(rows[0]["version"]) == 1

    # the context is still usable and the chain continues cleanly
    after = await repo.apply_versioned(
        _rec(key, "Incineration"), organization_id=org, actor_id=actor, context_key=key,
        evidence_signature="sig-r067")
    rows = await _lineage(pool, org, key)
    assert [int(r["version"]) for r in rows] == [1, 2]
    assert sum(1 for r in rows if r["is_current"]) == 1
    assert str(after["supersedes_id"]) == str(seed["id"])


@pytest.mark.asyncio
async def test_d_failing_writer_concurrent_with_a_good_writer_stays_consistent(pool) -> None:
    """Contention + a failing transaction: one lineage, one current, chain intact."""
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    repo = ActivityClarificationsRepository(pool)
    actor = str(uuid.uuid4())
    await repo.apply_versioned(_rec(key, "Landfill"), organization_id=org, actor_id=actor,
                               context_key=key, evidence_signature="sig-r067")
    await _warm(pool, 2)

    good, bad = await asyncio.gather(
        repo.apply_versioned(_rec(key, "Incineration"), organization_id=org, actor_id=actor,
                             context_key=key, evidence_signature="sig-r067"),
        repo.apply_versioned(_rec(key, "Waste oils"), organization_id=org, actor_id=actor,
                             context_key=key, evidence_signature="sig-r067",
                             batch_key=str(uuid.uuid4())),
        return_exceptions=True,
    )
    assert isinstance(bad, asyncpg.ForeignKeyViolationError), bad
    assert not isinstance(good, BaseException), good

    rows = await _lineage(pool, org, key)
    assert len({str(r["adjudication_id"]) for r in rows}) == 1
    assert sum(1 for r in rows if r["is_current"]) == 1
    assert [int(r["version"]) for r in rows] == [1, 2]       # no orphan from the failure
    assert rows[1]["clarification"] == "Incineration"



@pytest.mark.asyncio
async def test_d_a_writer_that_bypasses_the_lock_cannot_fork_the_context(pool) -> None:
    """The unique index — not application discipline — makes a second lineage impossible."""
    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    repo = ActivityClarificationsRepository(pool)
    await repo.apply_versioned(_rec(key, "Landfill"), organization_id=org,
                               actor_id=str(uuid.uuid4()), context_key=key,
                               evidence_signature="sig-r067")

    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.UniqueViolationError) as exc:
            # Same bounded context, a DIFFERENT clarification/version, so only the
            # context index can reject it (the replay key cannot).
            await conn.execute(
                "INSERT INTO public.activity_clarifications "
                "(activity_key, organization_id, original_activity, clarification, "
                " policy_input, outcome_status, adjudication_id, effective_context_key, "
                " version, is_current) "
                "VALUES ($1,$2,'Waste','Composting','Waste Composting','selected',$3,$1,2,true)",
                key, org, uuid.uuid4())
    assert exc.value.constraint_name == "activity_clarifications_context_unique"

    # the repository still versions the ONE lineage that exists (no second current row)
    converged = await repo.apply_versioned(_rec(key, "Incineration"), organization_id=org,
                                           actor_id=str(uuid.uuid4()), context_key=key,
                                           evidence_signature="sig-r067")
    rows = await _lineage(pool, org, key)
    assert len(rows) == 2                                    # retired v1 + new v2
    assert str(converged["supersedes_id"]) == str(rows[0]["id"])
    assert str(converged["adjudication_id"]) == str(rows[0]["adjudication_id"])
    assert [int(r["version"]) for r in rows] == [1, 2]
    assert sum(1 for r in rows if r["is_current"]) == 1


@pytest.mark.asyncio
async def test_d_bounded_retry_converges_without_timing_dependence(pool) -> None:
    """The convergence retry is proven deterministically (no race, no timing)."""
    from data.activity_clarifications import _ContextConvergenceRetry  # noqa: PLC0415

    org = await _new_org(pool)
    key = f"f0391-067:{uuid.uuid4()}"
    actor = str(uuid.uuid4())

    class _FirstAttemptLoses(ActivityClarificationsRepository):
        """Injects the exact signal a lost context race produces, once."""

        def __init__(self, pool_):
            super().__init__(pool_)
            self.attempts = 0

        async def _apply_versioned_once(self, *args, **kwargs):
            self.attempts += 1
            if self.attempts == 1:
                raise _ContextConvergenceRetry("injected")
            return await super()._apply_versioned_once(*args, **kwargs)

    repo = _FirstAttemptLoses(pool)
    first = await repo.apply_versioned(_rec(key, "Landfill"), organization_id=org,
                                       actor_id=actor, context_key=key,
                                       evidence_signature="sig-r067")
    assert repo.attempts == 2                     # one lost attempt, then convergence
    rows = await _lineage(pool, org, key)
    assert len(rows) == 1 and rows[0]["id"] == first["id"]

    class _AlwaysLoses(ActivityClarificationsRepository):
        async def _apply_versioned_once(self, *args, **kwargs):
            raise _ContextConvergenceRetry("injected")

    with pytest.raises(AdjudicationConcurrencyConflict):
        await _AlwaysLoses(pool).apply_versioned(
            _rec(key, "Incineration"), organization_id=org, actor_id=actor,
            context_key=key, evidence_signature="sig-r067")
    rows = await _lineage(pool, org, key)
    assert len(rows) == 1 and rows[0]["is_current"] is True   # nothing was written



# ---------------------------------------------------------------------------
# TEST E — an explicitly warm pool must not mask the race
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e_race_is_detected_with_an_already_warm_pool(pool) -> None:
    """Two consecutive races in one session — the second runs on a fully warm pool."""
    org = await _new_org(pool)
    for round_no in range(2):
        key = f"f0391-067:{uuid.uuid4()}"
        await _warm(pool, 5)                     # connections are already established
        results = await _race(pool, org, key, _DISTINCT)
        assert not [r for r in results if isinstance(r, BaseException)], results
        rows = await _lineage(pool, org, key)
        assert len({str(r["adjudication_id"]) for r in rows}) == 1, f"round {round_no}"
        assert sum(1 for r in rows if r["is_current"]) == 1, f"round {round_no}"
        assert [int(r["version"]) for r in rows] == [1, 2, 3, 4, 5], f"round {round_no}"


# ---------------------------------------------------------------------------
# TEST F — the production API call shape must hold the same invariant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_f_api_concurrent_clarifications_converge_on_one_lineage(pool) -> None:
    """The production call shape: N concurrent POSTs for one bounded context."""
    await _seed_factors(pool)
    org = await _new_org(pool)
    item = await _new_item(pool, org)
    user = _member(org, str(uuid.uuid4()))
    base = {"organization_id": org, "activity": "Waste", "item_id": item}
    await _warm(pool, 5)

    async with _client(_api_app(pool, user=user)) as client:
        # The engine's OWN eligible semantic options — the API refuses anything else, so
        # the race must be driven with the real production choices.
        offered = await client.get(OPTIONS, params=base)
        assert offered.status_code == 200, offered.text
        terms = [o["semantic_term"] for o in offered.json()["options"]][:5]
        assert len(terms) >= 3, terms

        responses = await asyncio.gather(*[
            client.post(CLARIFY, json={**base, "clarification": term}) for term in terms
        ])
        assert [r.status_code for r in responses] == [201] * len(terms), \
            [r.text for r in responses]

        effective = await client.get(EFFECTIVE, params=base)
        history = await client.get(
            HISTORY, params={**base, "adjudication_id": str(
                effective.json()["adjudication"]["id"])})

    rows = await _lineage(pool, org, item)        # the API context key is the item id
    assert len({str(r["adjudication_id"]) for r in rows}) == 1
    assert sum(1 for r in rows if r["is_current"]) == 1
    assert [int(r["version"]) for r in rows] == list(range(1, len(terms) + 1))
    assert effective.status_code == 200
    assert effective.json()["adjudication"]["version"] == len(terms)
    assert [v["version"] for v in history.json()["versions"]] == \
        list(range(1, len(terms) + 1))

