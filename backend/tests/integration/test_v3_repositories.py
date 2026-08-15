"""Integration tests for the V3 repositories (ADR-V3-001/002/009).

Runs against the dedicated ``carbontally_test`` database (see
``tests/integration/conftest.py``) — never the authoritative development
database. Verifies CRUD + lifecycle persistence over the V3M-1 / V3M-3 /
V3M-5 tables, and that hard-delete is refused at the repository boundary.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from data.customer_factors import CustomerFactorsRepository
from data.issues import IssuesRepository
from data.processing_entities import ProcessingEntitiesRepository
from domain.customer_factor import CustomerFactor
from domain.entity import ProcessingEntity
from domain.issue import Issue
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


async def test_processing_entities_repo_lifecycle(pool) -> None:
    repo = ProcessingEntitiesRepository(pool)
    entity_id = new_id()
    entity = ProcessingEntity(id=entity_id, name="Babui Limited")
    stored = await repo.save(entity)
    assert stored.id == entity_id
    assert stored.status == "active"

    fetched = await repo.get(entity_id)
    assert fetched is not None and fetched.name == "Babui Limited"

    all_entities = await repo.list_all()
    assert any(e.id == entity_id for e in all_entities)

    suspended = await repo.update_status(entity_id, "suspended", updated_by=new_id())
    assert suspended.status == "suspended"

    by_status = await repo.list_by_status("suspended")
    assert any(e.id == entity_id for e in by_status)


async def test_processing_entities_repo_no_hard_delete(pool) -> None:
    repo = ProcessingEntitiesRepository(pool)
    entity = ProcessingEntity(id=new_id(), name="Never Deleted")
    await repo.save(entity)
    with pytest.raises(NotImplementedError):
        await repo.delete(entity.id)


async def test_customer_factors_repo_org_scope(pool) -> None:
    repo = CustomerFactorsRepository(pool)
    org_a = await make_org(pool)
    org_b = await make_org(pool)
    cf_id = new_id()
    factor = CustomerFactor(
        id=cf_id,
        organization_id=org_a,
        name="Electricity",
        activity_type="Electricity",
        co2e_multiplier=Decimal("0.31"),
        unit="kWh",
        scope="Scope 2",
        country="GB",
        reporting_year=2025,
        status="draft",
        version=1,
    )
    await repo.save(factor)

    org_a_factors = await repo.get_org_factors(org_a)
    assert len(org_a_factors) == 1
    org_b_factors = await repo.get_org_factors(org_b)
    assert len(org_b_factors) == 0

    # Draft factors are not matching candidates (D-cf-5).
    assert await repo.get_active_for_org(org_a) == []

    active = await repo.update_status(cf_id, "active", updated_by=new_id())
    assert active.status == "active"
    active_candidates = await repo.get_active_for_org(org_a)
    assert len(active_candidates) == 1
    assert active_candidates[0].id == cf_id


async def test_customer_factors_repo_no_hard_delete(pool) -> None:
    repo = CustomerFactorsRepository(pool)
    org = await make_org(pool)
    factor = CustomerFactor(
        id=new_id(),
        organization_id=org,
        name="Never Deleted",
        activity_type="Fuels > Petrol",
        co2e_multiplier=Decimal("2.30"),
        country="GB",
        reporting_year=2025,
    )
    await repo.save(factor)
    with pytest.raises(NotImplementedError):
        await repo.delete(factor.id)


async def test_issues_repo_scoped_queries(pool) -> None:
    repo = IssuesRepository(pool)
    org = await make_org(pool)
    issue_id = new_id()
    issue = Issue(
        id=issue_id,
        title="Missing page",
        organization_id=org,
        status="open",
    )
    await repo.save(issue)

    org_issues = await repo.list_for_org(org)
    assert len(org_issues) == 1
    assert org_issues[0].id == issue_id

    resolved = await repo.update_status(issue_id, "resolved", updated_by=new_id())
    assert resolved.status == "resolved"

    open_issues = await repo.list_open(organization_id=org)
    assert open_issues == []


async def test_issues_repo_no_hard_delete(pool) -> None:
    repo = IssuesRepository(pool)
    org = await make_org(pool)
    issue = Issue(id=new_id(), title="Never Deleted", organization_id=org)
    await repo.save(issue)
    with pytest.raises(NotImplementedError):
        await repo.delete(issue.id)
