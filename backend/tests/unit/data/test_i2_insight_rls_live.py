"""Live-schema Insight RLS regression (OHD F-03 / F-06).

Authorization: `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (bounded I1 hardening).

OHD F-06: the I1 suite was fake-repo API tests plus DDL-text assertions — it had
no live-schema RLS test, so the database boundary (the layer protecting the
`authenticated`/PostgREST client path) had no durable regression protection. This
module supplies it: it exercises the REAL policies against a REAL database.

SAFETY (AGENTS.md §55.1 / PO control F-046-1)
    The test is skipped unless `INSIGHT_RLS_TEST_DSN` is set, and it refuses to
    run against any database whose name looks persistent (`demo`, `qa`,
    `investor`, `prod`, `live`) or matches the main application databases. It
    performs NO destructive setup: one transaction, its own fixture rows, then
    rollback. It never TRUNCATEs, never deletes, and never touches the Demo Lab /
    QA / production databases.

Run (disposable database only), from `backend/`:

    INSIGHT_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:5432/carbontally_test \
        python -m pytest tests/unit/data/test_i2_insight_rls_live.py -q
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("asyncpg")
import asyncpg  # noqa: E402

_DSN_ENV = "INSIGHT_RLS_TEST_DSN"
_FORBIDDEN_MARKERS = ("demo", "qa", "investor", "prod", "live")
_FORBIDDEN_DATABASES = {
    "postgres",
    "carbon_ledger",
    "carbontally",
    "carbontally_demo_local",
    "carbontally_qa_phase8",
}

_ORG_A = "11111111-1111-4111-8111-111111111111"
_ORG_B = "22222222-2222-4222-8222-222222222222"
_ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_CONVERSATION = "aaaaaaaa-1111-4111-8111-111111111111"


def _dsn() -> str:
    dsn = os.environ.get(_DSN_ENV, "").strip()
    if not dsn:
        pytest.skip(
            f"{_DSN_ENV} is not set (the live RLS test runs only against a disposable database)"
        )
    database = dsn.rsplit("/", 1)[-1].split("?")[0].lower()
    if database in _FORBIDDEN_DATABASES or any(m in database for m in _FORBIDDEN_MARKERS):
        raise RuntimeError(
            f"{_DSN_ENV} names {database!r}: this test performs live RLS writes and may "
            "never target a persistent environment (AGENTS.md §55.1 / F-046-1). Use a "
            "disposable clone or the dedicated test database."
        )
    return dsn


@pytest.fixture()
async def conn():
    """One connection, one transaction, always rolled back."""
    connection = await asyncpg.connect(_dsn())
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


async def _seed(conn) -> None:
    await conn.execute(
        """
        INSERT INTO public.organizations (id, name) VALUES ($1, 'I2 RLS Org A'), ($2, 'I2 RLS Org B')
        ON CONFLICT (id) DO NOTHING
        """,
        _ORG_A,
        _ORG_B,
    )
    await conn.execute(
        """
        INSERT INTO public.users (id, email) VALUES
            ($1, 'i2-alice@example.test'), ($2, 'i2-bob@example.test')
        ON CONFLICT (id) DO NOTHING
        """,
        _ALICE,
        _BOB,
    )
    await conn.execute(
        """
        INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active)
        VALUES (gen_random_uuid(), $1, $2, 'owner', true), (gen_random_uuid(), $1, $3, 'member', true)
        ON CONFLICT DO NOTHING
        """,
        _ORG_A,
        _ALICE,
        _BOB,
    )
    await conn.execute(
        """
        INSERT INTO public.carbontally_insight_conversations (id, organization_id, created_by, title)
        VALUES ($1, $2, $3, 'live RLS conversation')
        ON CONFLICT (id) DO NOTHING
        """,
        _CONVERSATION,
        _ORG_A,
        _ALICE,
    )


async def _as(conn, user_id: str) -> None:
    """Role-play an authenticated client with the given JWT subject."""
    await conn.execute("SET LOCAL ROLE authenticated")
    await conn.execute(
        "SELECT set_config('request.jwt.claims', $1, true)", f'{{"sub":"{user_id}"}}'
    )


async def _reset_role(conn) -> None:
    await conn.execute("RESET ROLE")


async def test_client_may_persist_only_human_authored_messages(conn) -> None:
    """OHD F-03 — a client cannot forge the reserved author kind."""
    await _seed(conn)
    await _as(conn, _ALICE)

    human = await conn.execute(
        """
        INSERT INTO public.carbontally_insight_messages
            (conversation_id, organization_id, created_by, role, content, ordinal)
        VALUES ($1, $2, $3, 'user', 'authorized human message', 1)
        """,
        _CONVERSATION,
        _ORG_A,
        _ALICE,
    )
    assert human.startswith("INSERT")

    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
        # Nested transaction = SAVEPOINT: the RLS rejection aborts only the
        # savepoint, so the surrounding assertion transaction stays usable.
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO public.carbontally_insight_messages
                    (conversation_id, organization_id, created_by, role, content, ordinal)
                VALUES ($1, $2, $3, 'insight', 'forged insight message', 2)
                """,
                _CONVERSATION,
                _ORG_A,
                _ALICE,
            )
    await _reset_role(conn)


async def test_creator_private_visibility_holds_live(conn) -> None:
    await _seed(conn)
    await _as(conn, _ALICE)
    assert (
        await conn.fetchval("SELECT count(*) FROM public.carbontally_insight_conversations")
        == 1
    )
    await _reset_role(conn)

    await _as(conn, _BOB)  # same organisation, different creator
    assert (
        await conn.fetchval("SELECT count(*) FROM public.carbontally_insight_conversations")
        == 0
    )
    await _reset_role(conn)


async def test_cross_organisation_read_and_write_are_denied_live(conn) -> None:
    await _seed(conn)
    await _as(conn, _BOB)
    assert (
        await conn.fetchval("SELECT count(*) FROM public.carbontally_insight_messages") == 0
    )
    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
        # Nested transaction = SAVEPOINT: the RLS rejection aborts only the
        # savepoint, so the surrounding assertion transaction stays usable.
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO public.carbontally_insight_messages
                    (conversation_id, organization_id, created_by, role, content, ordinal)
                VALUES ($1, $2, $3, 'user', 'cross tenant', 1)
                """,
                _CONVERSATION,
                _ORG_B,
                _BOB,
            )
    await _reset_role(conn)


async def test_service_role_writes_the_reserved_author_kind(conn) -> None:
    """F-05 — the backend (service_role) remains the only writer of `insight`."""
    await _seed(conn)
    await conn.execute(
        """
        INSERT INTO public.carbontally_insight_messages
            (conversation_id, organization_id, created_by, role, content, ordinal)
        VALUES ($1, $2, $3, 'insight', 'backend-authored', 1)
        """,
        _CONVERSATION,
        _ORG_A,
        _ALICE,
    )
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_messages WHERE role = 'insight'"
        )
        == 1
    )
