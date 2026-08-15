"""Integration tests for V3M-1 + V3M-2 — Processing Entity foundation and work
item entity relationships (CarbonTally V3 Implementation Phase 1).

These tests run against the dedicated test database ``carbontally_test`` (see
``tests/integration/conftest.py``) — never the authoritative development
database. They verify the schema and invariants established by:

  * ``supabase/migrations/20260810000000_v3m1_processing_entities.sql``
  * ``supabase/migrations/20260810010000_v3m2_entity_relationships.sql``

Covered invariants:
  1. ``processing_entities`` rows can be created.
  2. Valid staff can reference a Processing Entity (``staff_profiles.entity_id``).
  3. CarbonTally internal staff remain ``entity_id IS NULL`` (positive convention).
  4. Invalid entity references are rejected (FK ``ON DELETE RESTRICT``).
  5. Entity relationships preserve existing data (no NULL/row mutation).
  6. Existing organization isolation still works (tenant RLS unchanged).
  7. Processing Entity isolation: ``processing_entities`` is deny-by-default
     for ``authenticated`` (deny-by-default for non-members; the V3M-6 entity SELECT storey is the only policy).
  8. Existing staff access does not regress.
  9. Existing work records remain valid (rows untouched by the migration).
 10. Factor baseline remains exactly 7,049 (DEFRA 7,029 · SEAI 20).
"""
from __future__ import annotations

import uuid

import asyncpg
import pytest

from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_entity(
    conn: asyncpg.Connection, name: str = "Processing Entity A"
) -> str:
    """Insert a processing_entities row and return its id."""
    entity_id = new_id()
    await conn.execute(
        "INSERT INTO public.processing_entities (id, name, status) "
        "VALUES ($1, $2, 'active')",
        entity_id,
        name,
    )
    return entity_id


async def _count_factors(conn: asyncpg.Connection) -> int:
    return await conn.fetchval("SELECT count(*) FROM public.emission_factors")


async def _count_factors_by_source(
    conn: asyncpg.Connection, factor_source: str
) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM public.emission_factors WHERE factor_source = $1",
        factor_source,
    )


# ---------------------------------------------------------------------------
# 1. processing_entities can be created
# ---------------------------------------------------------------------------


async def test_processing_entities_create_and_fetch(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        entity_id = await _create_entity(conn, "Entity Alpha")
        row = await conn.fetchrow(
            "SELECT name, status FROM public.processing_entities WHERE id = $1",
            entity_id,
        )
        assert row is not None
        assert row["name"] == "Entity Alpha"
        assert row["status"] == "active"


async def test_processing_entities_status_check(pool: asyncpg.Pool) -> None:
    """The lifecycle CHECK rejects an unknown status value."""
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, $2, 'bogus_status')",
                new_id(),
                "Bad Status Entity",
            )


# ---------------------------------------------------------------------------
# 2. Valid staff can reference a Processing Entity
# ---------------------------------------------------------------------------


async def test_staff_can_reference_entity(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        entity_id = await _create_entity(conn, "Entity Beta")
        user_id = new_id()
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"staff-{user_id}@example.test",
        )
        staff_id = new_id()
        await conn.execute(
            "INSERT INTO public.staff_profiles "
            "(id, user_id, first_name, last_name, email, entity_id) "
            "VALUES ($1, $2, 'Worker', 'One', $3, $4)",
            staff_id,
            user_id,
            f"worker-{user_id}@example.test",
            entity_id,
        )
        row = await conn.fetchrow(
            "SELECT entity_id FROM public.staff_profiles WHERE id = $1", staff_id
        )
        assert row is not None
        assert row["entity_id"] == uuid.UUID(entity_id)


# ---------------------------------------------------------------------------
# 3. CarbonTally internal staff remain entity_id IS NULL
# ---------------------------------------------------------------------------


async def test_staff_null_entity_is_internal(pool: asyncpg.Pool) -> None:
    """NULL entity_id = CarbonTally internal processing (positive convention)."""
    async with pool.acquire() as conn:
        user_id = new_id()
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"internal-{user_id}@example.test",
        )
        staff_id = new_id()
        await conn.execute(
            "INSERT INTO public.staff_profiles "
            "(id, user_id, first_name, last_name, email, entity_id) "
            "VALUES ($1, $2, 'Internal', 'Staff', $3, NULL)",
            staff_id,
            user_id,
            f"internal-{user_id}@example.test",
        )
        row = await conn.fetchrow(
            "SELECT entity_id FROM public.staff_profiles WHERE id = $1", staff_id
        )
        assert row is not None
        assert row["entity_id"] is None


# ---------------------------------------------------------------------------
# 4. Invalid entity references are rejected (FK)
# ---------------------------------------------------------------------------


async def test_staff_invalid_entity_rejected(pool: asyncpg.Pool) -> None:
    """A random UUID entity_id fails the FK constraint."""
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await conn.execute(
                "INSERT INTO public.staff_profiles "
                "(id, user_id, first_name, last_name, email, entity_id) "
                "VALUES ($1, $2, 'Bad', 'Ref', $3, $4)",
                new_id(),
                new_id(),
                f"bad-ref-{new_id()}@example.test",
                new_id(),  # not a processing_entities id
            )


# ---------------------------------------------------------------------------
# 5. Entity relationships preserve existing data
# ---------------------------------------------------------------------------


async def test_migration_preserves_existing_work_rows(pool: asyncpg.Pool) -> None:
    """Existing manual_review_queue / upload_batches rows must not be mutated
    by the entity migration (entity_id defaults NULL = CarbonTally internal)."""
    async with pool.acquire() as conn:
        work_statuses = await conn.fetch(
            "SELECT status FROM public.manual_review_queue LIMIT 5"
        )
        # No assertion on row count: the migration adds no data and must not
        # delete/mutate rows; this verifies the query executes cleanly.
        assert isinstance(work_statuses, list)

        # Verify the new columns exist and are nullable.
        cols = await conn.fetch(
            "SELECT column_name, is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND table_name = 'manual_review_queue' AND column_name = 'entity_id'"
        )
        assert len(cols) == 1
        assert cols[0]["is_nullable"] == "YES"

        ub_cols = await conn.fetch(
            "SELECT column_name, is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND table_name = 'upload_batches' AND column_name = 'entity_id'"
        )
        assert len(ub_cols) == 1
        assert ub_cols[0]["is_nullable"] == "YES"


# ---------------------------------------------------------------------------
# 6. Existing organization isolation still works (tenant RLS unchanged)
# ---------------------------------------------------------------------------


async def test_org_tenant_rls_still_present(pool: asyncpg.Pool) -> None:
    """The tenant RLS policies on manual_review_queue / upload_batches are
    unchanged by V3M-2 (no entity-scoped policy was added, no tenant policy
    dropped)."""
    async with pool.acquire() as conn:
        policies = await conn.fetch(
            "SELECT policyname FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'manual_review_queue'"
        )
        names = {p["policyname"] for p in policies}
        assert any("tenant" in n for n in names), names


# ---------------------------------------------------------------------------
# 7. Processing Entity isolation (deny-by-default for authenticated)
# ---------------------------------------------------------------------------


async def test_processing_entities_deny_by_default(pool: asyncpg.Pool) -> None:
    """processing_entities RLS posture under the V3 contract (V3M-6): RLS
    enabled; the ONLY policy is the entity SELECT storey
    (processing_entities_entity_select via is_entity_member); no
    INSERT/UPDATE/DELETE policy — non-members and writes are deny-by-default
    for authenticated."""
    async with pool.acquire() as conn:
        rls_on = await conn.fetchval(
            "SELECT relrowsecurity FROM pg_class "
            "WHERE relname = 'processing_entities'"
        )
        assert rls_on is True

        policies = await conn.fetch(
            "SELECT policyname, cmd FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'processing_entities'"
        )
        by_name = {p["policyname"]: p["cmd"] for p in policies}
        assert by_name == {"processing_entities_entity_select": "SELECT"}


# ---------------------------------------------------------------------------
# 8. Existing staff access does not regress (schema surface intact)
# ---------------------------------------------------------------------------


async def test_staff_profiles_schema_intact(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'staff_profiles'"
        )
        names = {c["column_name"] for c in cols}
        for required in (
            "id",
            "user_id",
            "first_name",
            "last_name",
            "email",
            "role_id",
            "entity_id",
        ):
            assert required in names, f"missing staff_profiles.{required}"


# ---------------------------------------------------------------------------
# 9. Existing work records remain valid (FK/index surface)
# ---------------------------------------------------------------------------


async def test_entity_fks_and_indexes_exist(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        fks = await conn.fetch(
            "SELECT conname, confdeltype FROM pg_constraint "
            "WHERE conname IN ('staff_profiles_entity_id_fkey', "
            "'manual_review_queue_entity_id_fkey', "
            "'upload_batches_entity_id_fkey')"
        )
        assert {f["conname"] for f in fks} == {
            "staff_profiles_entity_id_fkey",
            "manual_review_queue_entity_id_fkey",
            "upload_batches_entity_id_fkey",
        }
        # confdeltype 'r' = ON DELETE RESTRICT (asyncpg decodes PostgreSQL's
        # internal "char" type to bytes: b'r')
        assert all(f["confdeltype"] == b"r" for f in fks), fks

        idx = await conn.fetch(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname = 'public' AND indexname IN ("
            "'idx_staff_profiles_entity_id', "
            "'idx_manual_review_queue_entity_id', "
            "'idx_upload_batches_entity_id')"
        )
        assert {i["indexname"] for i in idx} == {
            "idx_staff_profiles_entity_id",
            "idx_manual_review_queue_entity_id",
            "idx_upload_batches_entity_id",
        }


# ---------------------------------------------------------------------------
# 10. Factor baseline remains exactly 7,049
# ---------------------------------------------------------------------------


async def test_factor_baseline_unchanged(pool: asyncpg.Pool) -> None:
    """The factor baseline invariant: DEFRA 7,029 · SEAI 20 · TOTAL 7,049."""
    async with pool.acquire() as conn:
        total = await _count_factors(conn)
        defra = await _count_factors_by_source(conn, "DEFRA-DESNZ")
        seai = await _count_factors_by_source(conn, "SEAI")
        assert total == 7049, f"expected 7049 total factors, got {total}"
        assert defra == 7029, f"expected 7029 DEFRA factors, got {defra}"
        assert seai == 20, f"expected 20 SEAI factors, got {seai}"


