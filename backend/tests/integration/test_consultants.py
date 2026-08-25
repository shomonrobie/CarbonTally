"""Integration tests for the V3 consultant repository surface (Phase 7).

Covers consultant profiles, firm membership, client grants (the
firm→organisation relationship model), client status updates and the
firm-member-by-user resolution used by the consultant authorization layer.
"""
from __future__ import annotations

import asyncpg
import pytest

from data.consultants import ConsultantsRepository
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


async def _make_user(pool: asyncpg.Pool) -> str:
    """Create a real ``users`` row (FK target for consultant columns)."""
    user_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"user-{user_id}@example.test",
        )
    return user_id


async def _seed_consultant(repo: ConsultantsRepository, pool: asyncpg.Pool, user_id: str):
    """Create a profile + firm member and return the profile id."""
    profile = await repo.create_profile(user_id, "Acme Consultants")
    await repo.add_firm_member(profile.id, user_id, "manager")
    return profile


async def test_profile_and_firm_member_roundtrip(pool: asyncpg.Pool) -> None:
    repo = ConsultantsRepository(pool)
    user_id = await _make_user(pool)
    profile = await repo.create_profile(user_id, "Acme Consultants")
    assert profile.user_id == user_id
    assert profile.is_active is True

    fetched = await repo.get_profile_by_user(user_id)
    assert fetched is not None
    assert fetched.id == profile.id

    member = await repo.get_firm_member_by_user(profile.id, user_id)
    assert member is not None
    assert member.role == "manager"


async def test_client_grant_relationship(pool: asyncpg.Pool) -> None:
    repo = ConsultantsRepository(pool)
    org_id = await make_org(pool)
    profile = await _seed_consultant(repo, pool, await _make_user(pool))

    client = await repo.add_client(
        profile.id, org_id, "ACME LTD", "Manufacturing", "acme@example.test", "Jane"
    )
    assert client.organization_id == org_id
    assert client.status in (None, "active")

    by_org = await repo.get_client_by_org(profile.id, org_id)
    assert by_org is not None
    assert by_org.id == client.id

    assert await repo.get_client_by_org(profile.id, new_id()) is None


async def test_update_client_status(pool: asyncpg.Pool) -> None:
    repo = ConsultantsRepository(pool)
    org_id = await make_org(pool)
    profile = await _seed_consultant(repo, pool, await _make_user(pool))
    client = await repo.add_client(profile.id, org_id, "ACME LTD")

    updated = await repo.update_client_status(client.id, "inactive")
    assert updated is not None
    assert updated.status == "inactive"

    assert await repo.update_client_status(new_id(), "inactive") is None


async def test_list_clients_firm_scoped(pool: asyncpg.Pool) -> None:
    repo = ConsultantsRepository(pool)
    org_a = await make_org(pool)
    org_b = await make_org(pool)
    profile_a = await _seed_consultant(repo, pool, await _make_user(pool))
    profile_b = await _seed_consultant(repo, pool, await _make_user(pool))
    await repo.add_client(profile_a.id, org_a, "Client A")
    await repo.add_client(profile_b.id, org_b, "Client B")

    ids_a = {c.organization_id for c in await repo.list_clients(profile_a.id)}
    assert ids_a == {org_a}
