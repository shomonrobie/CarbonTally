"""I4 remediation — LIVE PostgreSQL regression (OHD D-1/D-2/D-3/D-4).

Authorization: PO I4 bounded remediation (2026-09-21).

This suite applies the **shipped** migration to a real PostgreSQL database and
exercises the real repository SQL and the real HTTP route against it, because the
focused unit suites could not detect: an unapplicable migration (D-1), invalid
application SQL (D-2) or the asyncpg-jsonb decoding defect (D-3).

Safety (AGENTS.md §55.1 / F-046-1): the DSN is refused unless it names a
disposable database, and the suite **skips** when no DSN is configured — it never
falls back to a persistent environment. Each test runs in its own transaction
which is always rolled back.

Run (disposable database only), from ``backend/``::

    INSIGHT_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:54426/ct_i4_remediate_20260921 \
        python -m pytest tests/integration/test_i4_live_migration_and_persistence.py -q
"""
from __future__ import annotations

import json
import os
import pathlib
import uuid
from types import SimpleNamespace

import pytest

pytest.importorskip("asyncpg")
import asyncpg  # noqa: E402

from data.audit import AuditRepository  # noqa: E402
from data.insight import InsightRepository  # noqa: E402
from data.insight_interactions import InsightInteractionRepository  # noqa: E402

_DSN_ENV = "INSIGHT_RLS_TEST_DSN"
_FORBIDDEN_MARKERS = ("demo", "qa", "investor", "prod", "live")
_FORBIDDEN_DATABASES = {
    "postgres",
    "carbon_ledger",
    "carbontally",
    "carbontally_demo_local",
    "carbontally_qa_phase8",
}
_ROOT = pathlib.Path(__file__).resolve().parents[3]  # repository root
_MIGRATION = _ROOT / "supabase" / "migrations" / "20261003000000_p8_i4_insight_interactions.sql"


def _dsn() -> str:
    dsn = os.environ.get(_DSN_ENV, "").strip()
    if not dsn:
        pytest.skip(f"{_DSN_ENV} is not set (live I4 tests need a disposable database)")
    database = dsn.rsplit("/", 1)[-1].split("?")[0].lower()
    if database in _FORBIDDEN_DATABASES or any(m in database for m in _FORBIDDEN_MARKERS):
        raise RuntimeError(
            f"{_DSN_ENV} names {database!r}: live I4 tests may only target a disposable database"
        )
    return dsn


@pytest.fixture()
async def connection():
    conn = await asyncpg.connect(_dsn())
    tx = conn.transaction()
    await tx.start()
    try:
        yield conn
    finally:
        await tx.rollback()
        await conn.close()


class _ConnAdapter:
    """Makes a single asyncpg connection satisfy the pool adapter the
    repositories use (``async with pool.acquire() as conn``)."""

    def __init__(self, conn) -> None:
        self._conn = conn

    async def fetchrow(self, query, *args):
        return await self._conn.fetchrow(query, *args)

    async def fetch(self, query, *args):
        return await self._conn.fetch(query, *args)

    async def execute(self, query, *args):
        return await self._conn.execute(query, *args)


class _Acquire:
    def __init__(self, conn) -> None:
        self._conn = conn

    async def __aenter__(self):
        return _ConnAdapter(self._conn)

    async def __aexit__(self, *exc):
        return False


class _PoolAdapter:
    def __init__(self, conn) -> None:
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


async def _expect_rejected(connection, sql, *args):
    """Assert ``sql`` is rejected, without aborting the enclosing transaction:
    the failure is contained in a SAVEPOINT."""
    with pytest.raises(Exception):
        async with connection.transaction():
            await connection.execute(sql, *args)


async def _seed(conn, *, org_id, user_id, conversation_id, active=True):
    """Minimal, run-unique fixture: tenant, principal and one conversation.

    ``organization_members.user_id`` references ``public.users``, so the principal
    is seeded first. Both inserts fall back to the narrowest legal form so the
    fixture does not depend on optional columns.
    """
    await conn.execute(
        "INSERT INTO public.organizations (id, name, is_active) VALUES ($1, $2, $3)",
        org_id, f"I4 remediation {org_id[:8]}", active,
    )
    try:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, f"{user_id[:8]}@example.test",
        )
    except Exception:
        await conn.execute(
            "INSERT INTO public.users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
        )
    for role in ("owner", "member", "viewer"):
        try:
            await conn.execute(
                "INSERT INTO public.organization_members (organization_id, user_id, role)"
                " VALUES ($1, $2, $3)",
                org_id, user_id, role,
            )
            break
        except Exception:
            continue
    await conn.execute(
        "INSERT INTO public.carbontally_insight_conversations"
        " (id, organization_id, created_by, title) VALUES ($1, $2, $3, $4)",
        conversation_id, org_id, user_id, "I4 live remediation",
    )


# ---------------------------------------------------------------- D-1 / D-4 --
async def test_shipped_migration_applies_and_provisions_every_control(connection):
    await connection.execute(_MIGRATION.read_text())

    tables = {r["table_name"] for r in await connection.fetch(
        "select table_name from information_schema.tables"
        " where table_schema='public' and table_name like 'carbontally_insight%'"
    )}
    assert {
        "carbontally_insight_conversations",
        "carbontally_insight_messages",
        "carbontally_insight_interactions",
        "carbontally_insight_tool_calls",
    } <= tables

    rls = await connection.fetch(
        "select tablename, rowsecurity from pg_tables"
        " where schemaname='public' and tablename like 'carbontally_insight%'"
    )
    assert all(r["rowsecurity"] for r in rls)

    policies = await connection.fetch(
        "select policyname from pg_policies"
        " where schemaname='public' and tablename like 'carbontally_insight%'"
    )
    assert len(policies) >= 4

    triggers = {r["tgname"] for r in await connection.fetch(
        "select tgname from pg_trigger where not tgisinternal and tgname like 'ci_%'"
    )}
    assert {"ci_interactions_immutable", "ci_tool_calls_immutable"} <= triggers

    grants = {r["privilege_type"] for r in await connection.fetch(
        "select privilege_type from information_schema.role_table_grants"
        " where table_name='carbontally_insight_interactions' and grantee='authenticated'"
    )}
    assert {"SELECT", "INSERT"} <= grants
    assert "UPDATE" not in grants and "DELETE" not in grants

    columns = {r["column_name"] for r in await connection.fetch(
        "select column_name from information_schema.columns"
        " where table_schema='public' and table_name='carbontally_insight_tool_calls'"
    )}
    assert "references" in columns


# ------------------------------------------------------------- D-2 / D-3 ----
async def test_real_repository_round_trip_with_jsonb_references(connection):
    org, user, conversation = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    await _seed(connection, org_id=org, user_id=user, conversation_id=conversation)
    repo = InsightInteractionRepository(_PoolAdapter(connection))

    created = await repo.create_interaction(
        organization_id=org,
        conversation_id=conversation,
        created_by=user,
        question_hash="a" * 64,
        request_hash="b" * 64,
        idempotency_key="live-1",
        intent="report_lookup",
        intent_source="deterministic",
        message_id=None,
    )
    assert created.lifecycle == "received"
    assert created.metadata == {}          # jsonb decoded, not a string (D-3)
    await repo.mark_executing(interaction_id=created.id, organization_id=org)

    call = await repo.record_tool_call(          # D-2: INSERT with "references"
        interaction_id=created.id,
        organization_id=org,
        call_ordinal=1,
        tool_name="report_lookup",
        contract_version="i3-6point-v1",
        tool_status="success",
        arguments={"report_id": str(uuid.uuid4())},
        result_metadata={"status": "success", "item_count": 2},
        references=[{"kind": "report", "id": str(uuid.uuid4())}],
        arguments_hash="c" * 64,
        result_hash="d" * 64,
        result_item_count=2,
        truncated=False,
        duration_ms=7,
    )
    assert call.arguments["report_id"]
    assert call.result_metadata["item_count"] == 2
    assert len(call.references) == 1 and call.references[0]["kind"] == "report"

    # Idempotency: the same logical call must not duplicate evidence.
    again = await repo.record_tool_call(
        interaction_id=created.id,
        organization_id=org,
        call_ordinal=1,
        tool_name="report_lookup",
        contract_version="i3-6point-v1",
        tool_status="success",
        arguments={"report_id": call.arguments["report_id"]},
        result_metadata={"status": "success", "item_count": 2},
        references=[{"kind": "report", "id": call.references[0]["id"]}],
        arguments_hash="c" * 64,
        result_hash="d" * 64,
        result_item_count=2,
        truncated=False,
        duration_ms=9,
    )
    assert again.id == call.id

    listed = await repo.list_tool_calls(interaction_id=created.id, organization_id=org)
    assert len(listed) == 1
    assert listed[0].references == call.references          # round-trip (D-2/D-3)

    await repo.complete_interaction(
        interaction_id=created.id,
        organization_id=org,
        lifecycle="completed",
        answer_status="success",
        narration_state="skipped",
        tool_call_count=1,
        reference_count=1,
        metadata={"contract_version": "i4-layer2-v1"},
    )
    read = await repo.get_interaction(
        interaction_id=created.id, organization_id=org, created_by=user
    )
    assert read is not None and read.lifecycle == "completed"
    assert read.metadata == {"contract_version": "i4-layer2-v1"}


# -------------------------------------------------------------- immutability --
async def test_append_only_controls_are_enforced(connection):
    org, user, conversation = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    await _seed(connection, org_id=org, user_id=user, conversation_id=conversation)
    repo = InsightInteractionRepository(_PoolAdapter(connection))
    created = await repo.create_interaction(
        organization_id=org, conversation_id=conversation, created_by=user,
        question_hash="a" * 64, intent=None, intent_source="none",
    )
    await repo.complete_interaction(
        interaction_id=created.id, organization_id=org, lifecycle="failed",
        answer_status="error", narration_state="skipped",
    )
    await _expect_rejected(
        connection,
        "UPDATE public.carbontally_insight_interactions SET answer_status='success'"
        " WHERE id=$1", created.id,
    )
    await _expect_rejected(
        connection,
        "DELETE FROM public.carbontally_insight_interactions WHERE id=$1", created.id,
    )
    call = await repo.record_tool_call(
        interaction_id=created.id, organization_id=org, call_ordinal=1,
        tool_name="report_lookup", contract_version="i3-6point-v1",
        tool_status="error", arguments={}, result_metadata={}, references=[],
        arguments_hash="e" * 64, result_hash="f" * 64,
    )
    await _expect_rejected(
        connection,
        "UPDATE public.carbontally_insight_tool_calls SET tool_status='success' WHERE id=$1",
        call.id,
    )
    await _expect_rejected(
        connection,
        "DELETE FROM public.carbontally_insight_tool_calls WHERE id=$1", call.id,
    )


# ----------------------------------------------------------------------- RLS --
async def test_live_rls_smoke(connection):
    org_a, org_b = str(uuid.uuid4()), str(uuid.uuid4())
    alice, bob = str(uuid.uuid4()), str(uuid.uuid4())
    conversation = str(uuid.uuid4())
    await _seed(connection, org_id=org_a, user_id=alice, conversation_id=conversation)
    await _seed(
        connection, org_id=org_b, user_id=bob, conversation_id=str(uuid.uuid4())
    )
    repo = InsightInteractionRepository(_PoolAdapter(connection))
    created = await repo.create_interaction(
        organization_id=org_a, conversation_id=conversation, created_by=alice,
        question_hash="a" * 64, intent=None, intent_source="none",
    )

    async def _claims(uid):
        await connection.execute("SET LOCAL ROLE authenticated")
        await connection.execute(
            "SELECT set_config('request.jwt.claims', $1, true)",
            json.dumps({"sub": uid, "role": "authenticated"}),
        )

    await _claims(alice)
    visible = await connection.fetch(
        "SELECT id FROM public.carbontally_insight_interactions WHERE id=$1", created.id
    )
    assert [str(r["id"]) for r in visible] == [created.id]  # creator allowed
    await connection.execute("RESET ROLE")

    await _claims(bob)
    peer = await connection.fetch(
        "SELECT id FROM public.carbontally_insight_interactions WHERE id=$1", created.id
    )
    assert peer == []                                        # peer/cross-org denied
    await _expect_rejected(                                  # forged creator denied
        connection,
        "INSERT INTO public.carbontally_insight_interactions"
        " (organization_id, conversation_id, created_by, question_hash)"
        " VALUES ($1, $2, $3, $4)",
        org_a, conversation, alice, "a" * 64,
    )
    await connection.execute("RESET ROLE")

    # Anonymous denial: contained in a SAVEPOINT so the failure of the read does
    # not abort the enclosing test transaction.
    with pytest.raises(Exception):
        async with connection.transaction():
            await connection.execute("SET LOCAL ROLE anon")
            await connection.fetch(
                "SELECT id FROM public.carbontally_insight_interactions"
            )
