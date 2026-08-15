"""V3 RLS behaviour tests (authenticated role) — organisation / customer-factor /
processing-entity isolation.

These tests exercise the *behaviour* of the V3M-3/V3M-5/V3M-6 policies with a
real ``authenticated`` role, not just their existence. They run against the
dedicated ``carbontally_test`` database (see ``tests/integration/conftest.py``)
and emulate an authenticated session by setting ``request.jwt.claims``
(``auth.uid()`` reads the ``sub`` claim) and ``SET ROLE authenticated`` — the
same mechanism Supabase PostgREST uses.

No policy is weakened or bypassed; assertions verify the deny-by-default /
org-scoped / entity-scoped surfaces.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
import pytest

from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def _authenticated(
    pool: asyncpg.Pool, user_id: str
) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection in an ``authenticated`` session for ``user_id``.

    Emulates the Supabase PostgREST session (``SET ROLE authenticated`` +
    ``request.jwt.claims`` → ``auth.uid()``). The session state is reset on
    exit so pooled connections never leak the role or claims into other tests.
    """
    conn = await pool.acquire()
    try:
        await conn.execute("SET ROLE authenticated")
        claims = json.dumps({"sub": user_id, "role": "authenticated"})
        await conn.execute(
            "SELECT set_config('request.jwt.claims', $1, false)", claims
        )
        yield conn
    finally:
        await conn.execute("RESET ROLE")
        await conn.execute(
            "SELECT set_config('request.jwt.claims', '{}', false)"
        )
        await pool.release(conn)


async def _seed_org_member(pool, org_id: str, user_id: str, role: str = "member") -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"user-{user_id[:8]}@example.test",
        )
        await conn.execute(
            """
            INSERT INTO public.organization_members (
                id, organization_id, user_id, role, is_active, created_at
            ) VALUES ($1, $2, $3, $4, TRUE, NOW())
            """,
            new_id(),
            org_id,
            user_id,
            role,
        )


async def _seed_entity_staff(pool, user_id: str, entity_id: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"staff-{user_id[:8]}@example.test",
        )
        await conn.execute(
            """
            INSERT INTO public.staff_profiles (
                id, user_id, first_name, last_name, email, entity_id
            ) VALUES ($1, $2, 'Entity', 'Staff', $3, $4)
            """,
            new_id(),
            user_id,
            f"staff-{user_id[:8]}@example.test",
            entity_id,
        )


async def _count(conn: asyncpg.Connection, table: str, where: str, *args) -> int:
    return await conn.fetchval(
        f"SELECT count(*) FROM public.{table} WHERE {where}", *args
    )


# ---------------------------------------------------------------------------
# Organisation + customer-factor isolation (V3M-3 tenant policies)
# ---------------------------------------------------------------------------


class TestOrgAndCustomerFactorIsolation:
    async def test_org_member_sees_own_customer_factors(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        org_b = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_a,
            )
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'B', 'Gas', 0.1, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_b,
            )
        async with _authenticated(pool, member) as conn:
            # Own org rows are visible; the other org's rows are not.
            assert await _count(conn, "customer_factors", "organization_id = $1", org_a) == 1
            assert await _count(conn, "customer_factors", "organization_id = $1", org_b) == 0

    async def test_non_member_sees_nothing(self, pool: asyncpg.Pool) -> None:
        org_a = await make_org(pool)
        outsider = new_id()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_a,
            )
        async with _authenticated(pool, outsider) as conn:
            # No membership -> deny-by-default (no rows, no error).
            assert await _count(conn, "customer_factors", "organization_id = $1", org_a) == 0

    async def test_org_member_cannot_insert_into_other_org(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        org_b = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    """
                    INSERT INTO public.customer_factors (
                        id, organization_id, name, activity_type, co2e_multiplier,
                        country, reporting_year, factor_source, status, version
                    ) VALUES ($1, $2, 'x', 'Electricity', 0.2, 'GB', 2025,
                              'CUSTOMER', 'draft', 1)
                    """,
                    new_id(),
                    org_b,
                )


# ---------------------------------------------------------------------------
# Issues — org storey (V3M-5) + entity storey (V3M-6)
# ---------------------------------------------------------------------------


class TestIssueIsolation:
    async def test_org_member_sees_only_org_scoped_issues(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, organization_id, status)
                VALUES ($1, 'customer issue', $2, 'open')
                """,
                new_id(),
                org_a,
            )
        async with _authenticated(pool, member) as conn:
            # Org-scoped (entity_id IS NULL) rows are visible to the member.
            assert await _count(conn, "issues", "organization_id = $1", org_a) == 1

    async def test_entity_scoped_issues_not_customer_visible(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, organization_id, entity_id, status)
                VALUES ($1, 'entity issue', $2, $3, 'open')
                """,
                new_id(),
                org_a,
                entity_id,
            )
        async with _authenticated(pool, member) as conn:
            # The org storey excludes entity-scoped rows (never customer-visible).
            assert await _count(conn, "issues", "organization_id = $1", org_a) == 0

    async def test_entity_staff_sees_entity_scoped_issues(
        self, pool: asyncpg.Pool
    ) -> None:
        staff = new_id()
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, entity_id, status)
                VALUES ($1, 'entity issue', $2, 'open')
                """,
                new_id(),
                entity_id,
            )
        await _seed_entity_staff(pool, staff, entity_id)
        async with _authenticated(pool, staff) as conn:
            # V3M-6 entity storey: entity staff see their entity's issues.
            assert await _count(conn, "issues", "entity_id = $1", entity_id) == 1


# ---------------------------------------------------------------------------
# Processing Entity isolation (V3M-1 deny-by-default + V3M-6 is_entity_member)
# ---------------------------------------------------------------------------


class TestProcessingEntityIsolation:
    async def test_entity_deny_by_default_for_authenticated(
        self, pool: asyncpg.Pool
    ) -> None:
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
        async with _authenticated(pool, new_id()) as conn:
            # No entity staff membership -> deny-by-default.
            assert await _count(conn, "processing_entities", "id = $1", entity_id) == 0

    async def test_entity_staff_sees_own_entity(self, pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            staff = new_id()
        await _seed_entity_staff(pool, staff, entity_id)
        async with _authenticated(pool, staff) as conn:
            # is_entity_member(entity_id) resolves via staff_profiles.entity_id.
            assert await _count(conn, "processing_entities", "id = $1", entity_id) == 1

    async def test_entity_staff_does_not_see_other_entity(
        self, pool: asyncpg.Pool
    ) -> None:
        async with pool.acquire() as conn:
            entity_a = new_id()
            entity_b = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'A', 'active'), ($2, 'B', 'active')",
                entity_a,
                entity_b,
            )
            staff = new_id()
        await _seed_entity_staff(pool, staff, entity_a)
        async with _authenticated(pool, staff) as conn:
            assert await _count(conn, "processing_entities", "id = $1", entity_a) == 1
            assert await _count(conn, "processing_entities", "id = $1", entity_b) == 0


