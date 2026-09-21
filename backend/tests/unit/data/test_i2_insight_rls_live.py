"""Live-schema Insight RLS regression — HERMETIC (OHD I2 F-03 / I1 F-06).

Authorization: `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (bounded I1 hardening +
I2 remediation).

The database boundary (the layer protecting the `authenticated`/PostgREST client
path) is exercised against a REAL database. Hermeticity (OHD I2 F-03):

* every fixture id is a **fresh UUID per run**, so leftover rows from any other
  verification run can never collide with, or be counted by, this suite;
* every assertion is **scoped to this run's own rows** (its conversation id or
  its own organisation id) — no global `count(*)` over a shared table;
* a single transaction is opened per test and **always rolled back**; nothing is
  TRUNCATEd, deleted or mutated outside it;
* the DSN is refused unless it names a disposable database (never `demo`, `qa`,
  `investor`, `prod`, `live`, and never a main application database), and the
  suite skips when no DSN is configured — it never falls back to a persistent one.

Run (disposable database only), from `backend/`:

    INSIGHT_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:5432/carbontally_test \
        python -m pytest tests/unit/data/test_i2_insight_rls_live.py -q
"""
from __future__ import annotations

import os
import uuid

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


class _Fixture:
    """Fresh, run-unique ids — no dependence on any other run's leftovers."""

    def __init__(self) -> None:
        self.org_a = str(uuid.uuid4())
        self.org_b = str(uuid.uuid4())
        self.alice = str(uuid.uuid4())   # creator, member of org A
        self.bob = str(uuid.uuid4())     # non-creator member of org A
        self.conversation = str(uuid.uuid4())


@pytest.fixture()
async def fixture(conn):
    f = _Fixture()
    await conn.execute(
        "INSERT INTO public.organizations (id, name, is_active) VALUES ($1, 'I2-A', true), ($2, 'I2-B', true)",
        f.org_a,
        f.org_b,
    )
    await conn.execute(
        "INSERT INTO public.users (id, email) VALUES ($1, $2), ($3, $4)",
        f.alice,
        f"i2-{f.alice[:8]}@example.test",
        f.bob,
        f"i2-{f.bob[:8]}@example.test",
    )
    await conn.execute(
        "INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active) "
        "VALUES (gen_random_uuid(), $1, $2, 'owner', true), (gen_random_uuid(), $1, $3, 'member', true)",
        f.org_a,
        f.alice,
        f.bob,
    )
    await conn.execute(
        "INSERT INTO public.carbontally_insight_conversations (id, organization_id, created_by, title) "
        "VALUES ($1, $2, $3, 'hermetic fixture')",
        f.conversation,
        f.org_a,
        f.alice,
    )
    return f


async def _as(conn, user_id: str) -> None:
    """Role-play an authenticated client with the given JWT subject."""
    await conn.execute("SET LOCAL ROLE authenticated")
    await conn.execute(
        "SELECT set_config('request.jwt.claims', $1, true)", f'{{"sub":"{user_id}"}}'
    )


async def _reset_role(conn) -> None:
    await conn.execute("RESET ROLE")


def _insert_message(f, author: str, role: str, ordinal: int):
    return (
        "INSERT INTO public.carbontally_insight_messages "
        "(conversation_id, organization_id, created_by, role, content, ordinal) "
        "VALUES ($1, $2, $3, '" + role + "', 'body', " + str(ordinal) + ")"
    ), f.conversation, f.org_a, author


async def test_client_may_persist_only_human_authored_messages(conn, fixture) -> None:
    """OHD I1 F-03 — a client cannot forge the reserved author kind."""
    await _as(conn, fixture.alice)

    sql, *args = _insert_message(fixture, fixture.alice, "user", 1)
    assert (await conn.execute(sql, *args)).startswith("INSERT")

    forged_sql, *forged_args = _insert_message(fixture, fixture.alice, "insight", 2)
    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
        async with conn.transaction():  # SAVEPOINT: keeps the outer tx usable
            await conn.execute(forged_sql, *forged_args)

    # Scoped to this run's own conversation only.
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_messages WHERE conversation_id = $1",
            fixture.conversation,
        )
        == 1
    )
    await _reset_role(conn)


async def test_creator_private_visibility_holds_live(conn, fixture) -> None:
    await _as(conn, fixture.alice)
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_conversations WHERE id = $1",
            fixture.conversation,
        )
        == 1
    )
    await _reset_role(conn)

    await _as(conn, fixture.bob)  # same organisation, different creator
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_conversations WHERE id = $1",
            fixture.conversation,
        )
        == 0
    )
    await _reset_role(conn)


async def test_cross_organisation_read_and_write_are_denied_live(conn, fixture) -> None:
    await _as(conn, fixture.bob)
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_conversations WHERE organization_id = $1",
            fixture.org_b,
        )
        == 0
    )
    sql, *args = _insert_message(fixture, fixture.bob, "user", 1)
    with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
        async with conn.transaction():
            await conn.execute(sql, *args)
    await _reset_role(conn)


async def test_suspended_organisation_is_blocked_for_the_client_path(conn, fixture) -> None:
    """The RLS predicate agrees with the application's active-organisation rule.

    `public.is_org_member` requires an ACTIVE organisation, so a suspended
    organisation yields no rows for the authenticated client — the backend pool
    bypasses RLS, which is why `insight_authz` performs the explicit check
    (OHD I2 F-02).
    """
    await conn.execute(
        "UPDATE public.organizations SET is_active = false WHERE id = $1", fixture.org_a
    )
    await _as(conn, fixture.alice)
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_conversations WHERE id = $1",
            fixture.conversation,
        )
        == 0
    )
    await _reset_role(conn)


async def test_service_role_writes_the_reserved_author_kind(conn, fixture) -> None:
    """F-05 — the backend (service_role) remains the only writer of `insight`."""
    sql, *args = _insert_message(fixture, fixture.alice, "insight", 1)
    await conn.execute(sql, *args)
    assert (
        await conn.fetchval(
            "SELECT count(*) FROM public.carbontally_insight_messages "
            "WHERE conversation_id = $1 AND role = 'insight'",
            fixture.conversation,
        )
        == 1
    )
