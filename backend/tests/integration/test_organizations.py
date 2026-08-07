"""Integration tests for OrganizationsRepository."""
from __future__ import annotations

from datetime import datetime

import asyncpg
import pytest

from data.organizations import OrganizationsRepository
from domain.organization import Organization, OrganizationMetadata
from tests.integration.conftest import make_user, new_id

pytestmark = pytest.mark.asyncio


async def _org() -> Organization:
    return Organization(
        id=new_id(),
        name="Test Co",
        country="GB",
        is_active=True,
        created_at=datetime.now(),
    )


async def _insert_member(pool: asyncpg.Pool, org_id: str, role: str) -> str:
    member_id = new_id()
    user_id = await make_user(pool)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.organization_members
                (id, organization_id, user_id, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, TRUE, NOW())
            """,
            member_id,
            org_id,
            user_id,
            role,
        )
    return member_id


async def _insert_facility(pool: asyncpg.Pool, org_id: str) -> str:
    facility_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.facilities
                (id, organization_id, name, address_line1, city, postcode, is_active)
            VALUES ($1, $2, 'HQ', '1 Main St', 'London', 'SW1A 1AA', TRUE)
            """,
            facility_id,
            org_id,
        )
    return facility_id


async def _insert_asset(pool: asyncpg.Pool, org_id: str, facility_id: str) -> str:
    asset_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.assets
                (id, facility_id, organization_id, name, type, is_active)
            VALUES ($1, $2, $3, 'Boiler', 'boiler', TRUE)
            """,
            asset_id,
            facility_id,
            org_id,
        )
    return asset_id


async def test_save_and_get_round_trip(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org = await _org()
    saved = await repo.save(org)
    assert saved.id == org.id
    fetched = await repo.get(org.id)
    assert fetched is not None
    assert fetched.name == "Test Co"
    assert fetched.country == "GB"
    assert fetched.is_active is True
    assert await repo.get_by_id(org.id) is not None


async def test_get_missing_returns_none(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    assert await repo.get(new_id()) is None


async def test_get_members(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org = await _org()
    await repo.save(org)
    admin_id = await _insert_member(pool, org.id, "admin")
    viewer_id = await _insert_member(pool, org.id, "viewer")

    members = await repo.get_members(org.id)
    by_id = {m.id: m for m in members}
    assert set(by_id) == {admin_id, viewer_id}
    assert by_id[admin_id].role == "admin"
    assert by_id[viewer_id].role == "viewer"


async def test_metadata_upsert(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org = await _org()
    await repo.save(org)

    metadata = OrganizationMetadata(
        total_floor_area_sqm=1200.5,
        occupied_floor_area_sqm=900.0,
        fte_count=42,
        annual_revenue_gbp=1_500_000.0,
        sector="Professional services",
    )
    stored = await repo.update_metadata(org.id, metadata)
    assert stored.total_floor_area_sqm == 1200.5
    assert stored.fte_count == 42
    assert stored.sector == "Professional services"

    fetched = await repo.get_metadata(org.id)
    assert fetched is not None
    assert fetched.annual_revenue_gbp == 1_500_000.0

    # upsert path updates the same row
    updated = await repo.update_metadata(
        org.id,
        OrganizationMetadata(total_floor_area_sqm=1300.0),
    )
    assert updated.total_floor_area_sqm == 1300.0
    refreshed = await repo.get_metadata(org.id)
    assert refreshed is not None
    assert refreshed.total_floor_area_sqm == 1300.0


async def test_get_facilities_and_assets(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org = await _org()
    await repo.save(org)
    facility_id = await _insert_facility(pool, org.id)
    await _insert_asset(pool, org.id, facility_id)

    facilities = await repo.get_facilities(org.id)
    assert len(facilities) == 1
    facility = facilities[0]
    assert facility.name == "HQ"
    assert facility.postcode == "SW1A 1AA"
    assert facility.address == "1 Main St, London"

    assets = await repo.get_assets(org.id)
    assert len(assets) == 1
    assert assets[0].name == "Boiler"
    assert assets[0].asset_type == "boiler"
    assert assets[0].facility_id == facility_id


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org = await _org()
    await repo.save(org)
    await repo.delete(org.id)
    assert await repo.get(org.id) is None
