"""Integration tests for FactorAliasesRepository."""
from __future__ import annotations

import asyncpg
import pytest

from data.factor_aliases import FactorAliasesRepository
from domain.matching import FactorAlias
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


def _alias(**kwargs: object) -> FactorAlias:
    org_id = kwargs.get("organization_id")
    return FactorAlias(
        id=str(kwargs.get("id") or new_id()),
        organization_id=str(org_id) if org_id is not None else None,
        alias_text=str(kwargs.get("alias_text") or "petrol"),
        target_activity_type=str(kwargs.get("target_activity_type") or "Fuels > Petrol"),
        target_provider_key=str(kwargs.get("target_provider_key") or "defra"),
    )


async def test_save_global_alias_and_get(pool: asyncpg.Pool) -> None:
    repo = FactorAliasesRepository(pool)
    alias = _alias(organization_id=None)
    stored = await repo.save(alias)
    assert stored.id == alias.id
    fetched = await repo.get(alias.id)
    assert fetched is not None
    assert fetched.organization_id is None
    assert fetched.alias_text == "petrol"


async def test_find_by_alias_org_scoped_then_global(pool: asyncpg.Pool) -> None:
    repo = FactorAliasesRepository(pool)
    org_a = await make_org(pool)
    org_b = await make_org(pool)
    global_alias = _alias(organization_id=None, alias_text="derv")
    org_alias = _alias(
        organization_id=org_a, alias_text="derv", target_activity_type="Fuels > Org A Diesel"
    )
    await repo.save(global_alias)
    await repo.save(org_alias)

    for_org_a = await repo.find_by_alias("derv", org_a)
    assert for_org_a is not None
    assert for_org_a.target_activity_type == "Fuels > Org A Diesel"

    # org_b has no scoped alias -> falls back to the global one
    for_org_b = await repo.find_by_alias("derv", org_b)
    assert for_org_b is not None
    assert for_org_b.id == global_alias.id

    missing = await repo.find_by_alias("nope", org_a)
    assert missing is None


async def test_global_and_org_alias_lists(pool: asyncpg.Pool) -> None:
    repo = FactorAliasesRepository(pool)
    org = await make_org(pool)
    g1 = await repo.save(_alias(organization_id=None, alias_text="aa"))
    await repo.save(_alias(organization_id=None, alias_text="bb"))
    o1 = await repo.save(_alias(organization_id=org, alias_text="zz"))

    global_ids = {a.id for a in await repo.get_global_aliases()}
    assert g1.id in global_ids
    assert o1.id not in global_ids

    org_ids = {a.id for a in await repo.get_org_aliases(org)}
    assert o1.id in org_ids
    assert g1.id not in org_ids


async def test_save_updates_existing_alias(pool: asyncpg.Pool) -> None:
    repo = FactorAliasesRepository(pool)
    alias = _alias(organization_id=None, alias_text="heating")
    stored = await repo.save(alias)
    from dataclasses import replace

    renamed = replace(stored, target_activity_type="Fuels > Gas (updated)")
    saved = await repo.save(renamed)
    assert saved.target_activity_type == "Fuels > Gas (updated)"
    fetched = await repo.get(alias.id)
    assert fetched is not None
    assert fetched.target_activity_type == "Fuels > Gas (updated)"


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = FactorAliasesRepository(pool)
    alias = await repo.save(_alias(organization_id=None, alias_text="gone"))
    await repo.delete(alias.id)
    assert await repo.get(alias.id) is None
