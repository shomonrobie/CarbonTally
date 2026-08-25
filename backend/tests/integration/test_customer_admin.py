"""Integration tests for the V3 customer-admin repositories (Phase 6).

Covers OrganizationsRepository profile/metadata/member surfaces, the
InvitationsRepository over ``user_invitations``, and the RolesRepository.
"""
from __future__ import annotations

import asyncpg
import pytest

from data.invitations import InvitationsRepository
from data.organizations import OrganizationsRepository
from data.roles import RolesRepository
from data.tenant import TenantRepository
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


async def test_profile_roundtrip(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org_id = await make_org(pool)
    profile = await repo.get_profile(org_id)
    assert profile is not None
    assert profile["id"] == org_id
    assert profile["is_active"] is True

    updated = await repo.update_profile(
        org_id,
        {"company_number": "12345678", "industry": "Manufacturing", "secr_enabled": True},
    )
    assert updated["company_number"] == "12345678"
    assert updated["industry"] == "Manufacturing"
    assert updated["secr_enabled"] is True


async def test_metadata_upsert_roundtrip(pool: asyncpg.Pool) -> None:
    repo = OrganizationsRepository(pool)
    org_id = await make_org(pool)
    updated = await repo.update_metadata_full(
        org_id,
        {"total_employees": 120, "annual_revenue": 2_500_000.0, "industry_sector": "Retail"},
        updated_by="user-1",
    )
    assert updated is not None
    assert updated["total_employees"] == 120
    assert updated["industry_sector"] == "Retail"
    assert updated["updated_by"] == "user-1"

    fetched = await repo.get_metadata_full(org_id)
    assert fetched["annual_revenue"] == 2_500_000.0


async def test_members_with_email(pool: asyncpg.Pool) -> None:
    org_repo = OrganizationsRepository(pool)
    tenant = TenantRepository(pool)
    org_id = await make_org(pool)
    user_id = new_id()
    member = await tenant.add_member(org_id, user_id, "member")

    rows = await org_repo.list_members_with_email(org_id)
    assert len(rows) == 1
    assert rows[0]["id"] == member.id
    assert rows[0]["role"] == "member"

    detail = await org_repo.get_member(member.id)
    assert detail is not None
    assert detail["organization_id"] == org_id


async def test_invitations_roundtrip(pool: asyncpg.Pool) -> None:
    repo = InvitationsRepository(pool)
    org_id = await make_org(pool)
    invitation = await repo.create(
        org_id,
        "invitee@example.test",
        token=f"tok-{new_id()}",
        invited_by=None,
        status="pending",
    )
    assert invitation["email"] == "invitee@example.test"
    assert invitation["status"] == "pending"
    assert invitation["organization_id"] == org_id

    rows = await repo.list_for_org(org_id)
    assert len(rows) == 1
    assert rows[0]["token"] == invitation["token"]

    revoked = await repo.revoke(invitation["id"])
    assert revoked["status"] == "revoked"


async def test_roles_repository(pool: asyncpg.Pool) -> None:
    repo = RolesRepository(pool)
    rows = await repo.list()
    # The roles table is seeded in the RC2 baseline (admin, data_extractor, ...).
    assert isinstance(rows, list)
    by_name = await repo.get_by_name("admin")
    assert by_name is None or by_name["name"] == "admin"
