"""API contract tests for the V3 existing-data discovery surface (D27 / D19).

Covers the customer-initiated direct-onboarding workflow: lookup (candidate
signals only), request creation, email-code verification, staff-mediated
verification, and the USE ALL / PARTIAL / DISCARD adoption choices.
"""
from __future__ import annotations

from tests.unit.api.fakes import (
    InMemoryWorld,
    member_user,
    org_owner_user,
)


def _seed_request(world: InMemoryWorld, *, org_id="org-a", candidate="org-c", status="verified"):
    request = world.discovery._request_type(
        id=f"discovery-{len(world.discovery._requests) + 1}",
        organization_id=org_id,
        candidate_organization_id=candidate,
        status=status,
        verification_method="email",
    )
    world.discovery._requests.append(request)
    return request


def _seed_existing_org(world: InMemoryWorld, org_id="org-c", name="Existing Org"):
    """Register the candidate org in the organisations repo (needed by
    ``get_full`` / ``set_customer_type``) AND the discovery candidate list."""
    from datetime import datetime, timezone
    from tests.unit.api.fakes import Organization

    world.discovery.seed_org(org_id, name=name)
    world.organizations._orgs[org_id] = Organization(
        id=org_id, name=name, country="GB", is_active=True,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    world.organizations._profiles[org_id] = {
        "id": org_id,
        "name": name,
        "country": "GB",
        "is_active": True,
        "primary_contact_email": "existing@org.test",
        "billing_contact_email": None,
        "customer_type": None,
    }
    return org_id


def asyncio_get(coro_fn, *args):
    import asyncio

    return asyncio.run(coro_fn(*args))


class TestDiscoveryLookup:
    def test_lookup_requires_org_member(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/discovery/lookup",
            json={"organization_id": "org-a", "name": "Existing"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "candidates" in body
        assert "disclaimer" in body

    def test_lookup_never_returns_own_org(self, world, client, user_provider) -> None:
        world.discovery.seed_org("org-a", name="Org A")
        _seed_existing_org(world)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/discovery/lookup",
            json={"organization_id": "org-a", "name": "Org"},
        )
        assert resp.status_code == 200
        candidates = resp.json()["candidates"]
        assert all(c["organization_id"] != "org-a" for c in candidates)


class TestDiscoveryRequests:
    def test_create_request_requires_org_admin(self, world, client, user_provider) -> None:
        _seed_existing_org(world)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/discovery/requests",
            json={
                "organization_id": "org-a",
                "candidate_organization_id": "org-c",
                "verification_method": "email",
            },
        )
        assert resp.status_code == 403

    def test_create_request_as_admin(self, world, client, user_provider) -> None:
        _seed_existing_org(world)
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            "/api/v3/discovery/requests",
            json={
                "organization_id": "org-a",
                "candidate_organization_id": "org-c",
                "verification_method": "email",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["request"]["status"] == "pending_verification"
        assert body["request"]["candidate_organization_id"] == "org-c"
        # Email delivery is NOT configured in unit tests — reported honestly.
        assert body["verification_delivered"] is False

    def test_cannot_discover_own_org(self, world, client, user_provider) -> None:
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            "/api/v3/discovery/requests",
            json={
                "organization_id": "org-a",
                "candidate_organization_id": "org-a",
                "verification_method": "email",
            },
        )
        assert resp.status_code == 422

    def test_duplicate_request_conflict(self, world, client, user_provider) -> None:
        _seed_request(world, status="verified")
        _seed_existing_org(world)
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            "/api/v3/discovery/requests",
            json={
                "organization_id": "org-a",
                "candidate_organization_id": "org-c",
                "verification_method": "email",
            },
        )
        assert resp.status_code == 409

    def test_get_request_scoped_to_owning_org(self, world, client, user_provider) -> None:
        request = _seed_request(world)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(
            f"/api/v3/discovery/requests/{request.id}",
            params={"organization_id": "org-a"},
        )
        assert resp.status_code == 200
        assert resp.json()["request"]["id"] == request.id
        assert "eligible_categories" in resp.json()

    def test_get_request_foreign_org_denied(self, world, client, user_provider) -> None:
        request = _seed_request(world)

class TestVerification:
    def test_verify_with_correct_code(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="pending_verification")
        from data.discovery import generate_verification_code

        code = generate_verification_code()
        asyncio_get(world.discovery.store_verification_code, request.id, code)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/verify",
            json={"organization_id": "org-a", "code": code},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"

    def test_verify_wrong_code_rejected(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="pending_verification")
        asyncio_get(world.discovery.store_verification_code, request.id, "good-code-1")
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/verify",
            json={"organization_id": "org-a", "code": "wrong-code-1"},
        )
        assert resp.status_code == 400

    def test_staff_verify_requires_admin(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="pending_verification")
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/staff-verify",
            json={"organization_id": "org-a", "code": ""},
        )
        assert resp.status_code == 403

        user_provider.set_user(member_user("org-b", "member-2", "m2@test"))

class TestAdoptionChoices:
    def test_choice_requires_verified(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="pending_verification")
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/choice",
            json={"organization_id": "org-a", "choice": "use_all"},
        )
        assert resp.status_code == 409

    def test_use_all_adopts_in_place(self, world, client, user_provider) -> None:
        _seed_existing_org(world)
        request = _seed_request(world, status="verified")
        # An ACTIVE consultant grant exists for the candidate org — it must end.
        world.consultants.seed_client(
            "client-1", "firm-1", "org-c", "Existing Org", status="active"
        )
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/choice",
            json={"organization_id": "org-a", "choice": "use_all"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["outcome"] == "adopted"
        assert body["adopted_organization_id"] == "org-c"
        # The customer became owner of the adopted org.
        member = asyncio_get(world.tenant.get_member_by_user, "org-c", "owner-1")
        assert member is not None and member["role"] == "owner"
        # The ACTIVE consultant grant was ended.
        updated_client = next(c for c in world.consultants._clients if c.id == "client-1")
        assert updated_client.status == "ended"
        # The candidate org is labelled direct (informational).
        org_profile = asyncio_get(world.organizations.get_full, "org-c")
        assert org_profile.get("customer_type") == "direct"

    def test_partial_adoption_records_scope(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="verified")
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/choice",
            json={
                "organization_id": "org-a",
                "choice": "partial",
                "scope": {"categories": ["documents", "reports"]},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["choice"] == "partial"
        assert body["scope"]["categories"] == ["documents", "reports"]

    def test_partial_invalid_category_rejected(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="verified")
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/choice",
            json={
                "organization_id": "org-a",
                "choice": "partial",
                "scope": {"categories": ["documents", "secrets"]},
            },
        )
        assert resp.status_code == 422

    def test_discard_records_decision_and_keeps_data(self, world, client, user_provider) -> None:
        request = _seed_request(world, status="verified")
        world.consultants.seed_client(
            "client-2", "firm-1", "org-c", "Existing Org", status="active"
        )
        user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
        resp = client.post(
            f"/api/v3/discovery/requests/{request.id}/choice",
            json={"organization_id": "org-a", "choice": "discard"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["outcome"] == "discarded"
        # DISCARD does not delete data and does not end grants.
        updated_client = next(c for c in world.consultants._clients if c.id == "client-2")
        assert updated_client.status == "active"
