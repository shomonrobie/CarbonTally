"""API contract tests for the V3 customer-factor surface (ADR-V3-002)."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from tests.unit.api.fakes import (
    CustomerFactor,
    InMemoryWorld,
    admin_user,
    member_user,
)


def _await(coro) -> None:
    asyncio.run(coro)


def _seed_factor(*, factor_id: str = "cf-1", created_by: str = "member-1") -> CustomerFactor:
    return CustomerFactor(
        id=factor_id,
        organization_id="org-a",
        name="My Electricity Factor",
        activity_type="Electricity",
        co2e_multiplier=Decimal("0.31"),
        unit="kWh",
        scope="Scope 2",
        country="GB",
        reporting_year=2025,
        status="draft",
        created_by=created_by,
    )


class TestV3CustomerFactors:
    def test_create_factor_as_draft(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/customer-factors",
            json={
                "organization_id": "org-a",
                "name": "My Electricity Factor",
                "activity_type": "Electricity",
                "co2e_multiplier": "0.31",
                "reporting_year": 2025,
                "unit": "kWh",
                "scope": "Scope 2",
                "country": "GB",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "draft"
        assert body["factor_source"] == "CUSTOMER"
        assert body["organization_id"] == "org-a"

    def test_create_factor_invalid_country_rejected(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/customer-factors",
            json={
                "organization_id": "org-a",
                "name": "Invalid Country",
                "activity_type": "Electricity",
                "co2e_multiplier": "0.31",
                "reporting_year": 2025,
                "country": "FR",
            },
        )
        assert resp.status_code == 422

    def test_update_factor_negative_multiplier_rejected(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        # dataclasses.replace bypasses CustomerFactor.__post_init__, so the
        # wired A-ext validation (validate_customer_factor) is the guard that
        # rejects the negative multiplier with HTTP 422.
        _await(world.customer_factors.save(_seed_factor()))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put(
            "/api/v3/customer-factors/cf-1",
            json={"co2e_multiplier": "-1"},
        )
        assert resp.status_code == 422

    def test_list_factors_org_scoped(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.customer_factors.save(_seed_factor()))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get("/api/v3/customer-factors", params={"organization_id": "org-a"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["factors"][0]["id"] == "cf-1"

    def test_update_draft_factor(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.customer_factors.save(_seed_factor()))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put("/api/v3/customer-factors/cf-1", json={"name": "Renamed"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"

    def test_update_active_factor_rejected(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.customer_factors.save(_seed_factor(factor_id="cf-active")))
        _await(world.customer_factors.update_status("cf-active", "active", updated_by="admin-1"))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put("/api/v3/customer-factors/cf-active", json={"name": "Renamed"})
        assert resp.status_code == 409

    def test_approve_factor(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.customer_factors.save(_seed_factor()))  # created_by=member-1
        # Approver is a system admin (not the creator) — D-cf-3 authority.
        user_provider.set_user(admin_user())
        resp = client.post("/api/v3/customer-factors/cf-1/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_approve_own_factor_rejected(self, world: InMemoryWorld, client, user_provider) -> None:
        # Factor created by admin-1; admin attempts self-approval -> 403.
        _await(world.customer_factors.save(_seed_factor(created_by="admin-1")))
        user_provider.set_user(admin_user())
        resp = client.post("/api/v3/customer-factors/cf-1/approve")
        assert resp.status_code == 403

    def test_deactivate_factor(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.customer_factors.save(_seed_factor(factor_id="cf-active")))
        _await(world.customer_factors.update_status("cf-active", "active", updated_by="admin-1"))
        user_provider.set_user(admin_user())
        resp = client.post("/api/v3/customer-factors/cf-active/deactivate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "inactive"
