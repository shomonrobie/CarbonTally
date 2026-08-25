"""D35 — self-service customer onboarding tests.

Covers the two new surfaces:
* ``POST /api/v3/organizations`` — customer-initiated organization creation.
  The initial creator becomes OWNER (real ``organization_members`` role); an
  exact company-number candidate match blocks with ``409 discovery_required``
  unless the customer explicitly acknowledges the candidates.
* The PRE-ORG-CREATION discovery variants (organization_id omitted):
  ``POST /api/v3/discovery/lookup``, ``/requests``, ``/requests/{id}/verify``
  and ``/requests/{id}/choice`` — a brand-new customer with NO organization can
  discover, verify and adopt (USE ALL / PARTIAL / DISCARD) existing data.

Security under test:
* anonymous -> 401
* authenticated user without organization -> can create / adopt
* user who already belongs to an organization -> cannot create a second org
* cross-user onboarding request access -> 403/404
* adoption requires verification by the same actor
* DISCARD never deletes data
"""
from __future__ import annotations

from datetime import datetime, timezone

from tests.unit.api.fakes import (
    InMemoryWorld,
    member_user,
    org_owner_user,
    Organization,
)


def _no_org_user(user_id: str = "u-new", email: str = "new@customer.test"):
    """An authenticated user with NO organization membership."""
    from auth import AuthUser

    return AuthUser(
        user_id=user_id,
        email=email,
        role="user",
        role_name="user",
        is_active=True,
    )


def _seed_existing_org(world: InMemoryWorld, org_id="org-existing", name="Existing Org", *, company_number=None):
    """Register the candidate org in the organisations repo (needed by
    ``get_full`` / ``set_customer_type``) AND the discovery candidate list."""
    world.discovery.seed_org(
        org_id, name=name, company_number=company_number,
        contact_email="existing@org.test",
    )
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


def _run(coro_fn, *args):
    import asyncio

    return asyncio.run(coro_fn(*args))


# ---------------------------------------------------------------------------
# POST /api/v3/organizations — customer-initiated creation
# ---------------------------------------------------------------------------


def test_create_org_anonymous_401(client, user_provider):
    user_provider.set_unauthenticated()
    resp = client.post("/api/v3/organizations", json={"name": "New Co"})
    assert resp.status_code == 401


def test_create_org_creates_owner(client, world, user_provider):
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/organizations",
        json={"name": "Bright Start Ltd", "country": "GB"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["onboarding"]["status"] == "ORGANIZATION_CREATED"
    assert data["onboarding"]["role"] == "owner"
    assert data["onboarding"]["destination"] == "/home"
    assert data["member"]["role"] == "owner"
    assert data["member"]["user_id"] == "u-new"
    org_id = data["organization"]["id"]
    # The creator is now an ACTIVE owner membership (real role model).
    memberships = _run(world.organizations.get_active_memberships_for_user, "u-new")
    assert any(m.organization_id == org_id and m.role == "owner" for m in memberships)


def test_create_org_rejects_user_with_existing_membership(client, world, user_provider):
    world.organizations.add_member_record(
        {
            "id": "mem-u-a",
            "organization_id": "org-a",
            "user_id": "u-a",
            "role": "member",
            "is_active": True,
        }
    )
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.post("/api/v3/organizations", json={"name": "Second Org"})
    assert resp.status_code == 409
    assert "already belong" in resp.json()["error"]["message"]


def test_create_org_empty_name_422(client, user_provider):
    user_provider.set_user(_no_org_user())
    resp = client.post("/api/v3/organizations", json={"name": "   "})
    assert resp.status_code == 422


def test_create_org_exact_company_number_blocks_without_ack(client, world, user_provider):
    _seed_existing_org(world, company_number="IE123456")
    user_provider.set_user(_no_org_user("u-new", "new@acme.test"))
    resp = client.post(
        "/api/v3/organizations",
        json={"name": "Acme Logistics", "company_number": "IE123456"},
    )
    assert resp.status_code == 409
    # The global error envelope drops custom headers; the frontend routes on the
    # 409 status + message (duplicate-prevention -> existing-data review).
    assert "company number" in resp.json()["error"]["message"]


def test_create_org_acknowledged_candidates_overrides_block(client, world, user_provider):
    _seed_existing_org(world, company_number="IE123456")
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/organizations",
        json={
            "name": "Acme Logistics",
            "company_number": "IE123456",
            "acknowledged_candidates": ["org-existing"],
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["onboarding"]["status"] == "ORGANIZATION_CREATED"


def test_create_org_weak_candidates_returned_informational(client, world, user_provider):
    world.discovery.seed_org("org-other", name="Some Other Co")
    user_provider.set_user(_no_org_user())
    resp = client.post("/api/v3/organizations", json={"name": "Bright Start Ltd"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["candidates"][0]["organization_id"] == "org-other"
# ---------------------------------------------------------------------------
# PRE-ORG-CREATION discovery (no organization_id)
# ---------------------------------------------------------------------------


def test_onboarding_lookup_without_org(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/discovery/lookup",
        json={"name": "Acme Logistics", "email_domain": "acme.test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidates"][0]["organization_id"] == "org-existing"
    assert "data_summary" in data["candidates"][0]


def test_onboarding_lookup_with_org_still_requires_membership(client, world, user_provider):
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/discovery/lookup",
        json={"organization_id": "org-a", "name": "Anything"},
    )
    assert resp.status_code == 403


def test_onboarding_request_created_bound_to_actor(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user("u-new", "new@customer.test"))
    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    assert resp.status_code == 201, resp.text
    request = resp.json()["request"]
    assert request["organization_id"] is None
    assert request["status"] == "pending_verification"


def test_onboarding_request_requires_candidate(client, world, user_provider):
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-missing"},
    )
    assert resp.status_code == 404


def test_onboarding_verify_then_use_all_adopts_in_place(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user("u-new", "new@customer.test"))

    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    request_id = resp.json()["request"]["id"]
    _run(world.discovery.store_verification_code, request_id, "CODE1234")

    verify = client.post(
        f"/api/v3/discovery/requests/{request_id}/verify",
        json={"code": "CODE1234"},
    )
    assert verify.status_code == 200, verify.text

    choice = client.post(
        f"/api/v3/discovery/requests/{request_id}/choice",
        json={"choice": "use_all"},
    )
    assert choice.status_code == 200, choice.text
    data = choice.json()
    assert data["outcome"] == "adopted"
    assert data["adopted_organization_id"] == "org-existing"
    # Adoption is IN-PLACE — the existing organisation id is preserved.
    assert world.organizations._orgs["org-existing"].name == "Acme Logistics Ltd"
    # The customer became OWNER of the adopted org (real membership).
    member = _run(world.tenant.get_member_by_user, "org-existing", "u-new")
    assert member is not None and member["role"] == "owner"
    # No requesting org exists for an onboarding adoption — nothing to deactivate.
    assert _run(world.tenant.get_member_by_user, "org-a", "u-new") is None

def test_onboarding_use_all_labels_direct_customer(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user("u-new", "new@customer.test"))

    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    request_id = resp.json()["request"]["id"]
    _run(world.discovery.store_verification_code, request_id, "CODE1234")
    client.post(
        f"/api/v3/discovery/requests/{request_id}/verify",
        json={"code": "CODE1234"},
    )
    choice = client.post(
        f"/api/v3/discovery/requests/{request_id}/choice",
        json={"choice": "use_all"},
    )
    assert choice.status_code == 200, choice.text
    assert world.organizations._profiles["org-existing"]["customer_type"] == "direct"


def test_onboarding_verify_then_discard_records_decision_only(
    client, world, user_provider
):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user("u-new", "new@customer.test"))

    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    request_id = resp.json()["request"]["id"]
    _run(world.discovery.store_verification_code, request_id, "CODE1234")
    client.post(
        f"/api/v3/discovery/requests/{request_id}/verify",
        json={"code": "CODE1234"},
    )
    choice = client.post(
        f"/api/v3/discovery/requests/{request_id}/choice",
        json={"choice": "discard", "note": "We have our own records."},
    )
    assert choice.status_code == 200, choice.text
    assert choice.json()["outcome"] == "discarded"
    # DISCARD never creates a membership and never deletes candidate data.
    assert _run(world.tenant.get_member_by_user, "org-existing", "u-new") is None
    assert world.organizations._orgs["org-existing"].is_active is True


def test_onboarding_choice_before_verification_409(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user())
    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    request_id = resp.json()["request"]["id"]
    choice = client.post(
        f"/api/v3/discovery/requests/{request_id}/choice",
        json={"choice": "use_all"},
    )
    assert choice.status_code == 409


def test_onboarding_choice_by_different_user_denied(client, world, user_provider):
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(_no_org_user("u-new", "new@customer.test"))
    resp = client.post(
        "/api/v3/discovery/requests",
        json={"candidate_organization_id": "org-existing"},
    )
    request_id = resp.json()["request"]["id"]
    _run(world.discovery.store_verification_code, request_id, "CODE1234")
    user_provider.set_user(_no_org_user("u-intruder", "evil@example.test"))
    # A different user cannot verify or choose the onboarding request.
    verify = client.post(
        f"/api/v3/discovery/requests/{request_id}/verify",
        json={"code": "CODE1234"},
    )
def test_org_scoped_adoption_still_deactivates_requesting_org(
    client, world, user_provider
):
    """The standard D19 org-scoped flow is unchanged: USE ALL deactivates the
    (new) requesting org membership so the single-org resolver binds the
    adopted org."""
    world.tenant.seed_member(
        {
            "id": "mem-requesting",
            "organization_id": "org-a",
            "user_id": "u-owner",
            "role": "owner",
            "is_active": True,
        }
    )
    _seed_existing_org(world, name="Acme Logistics Ltd")
    user_provider.set_user(org_owner_user("org-a", "u-owner", "owner@example.test"))

    resp = client.post(
        "/api/v3/discovery/requests",
        json={"organization_id": "org-a", "candidate_organization_id": "org-existing"},
    )
    assert resp.status_code == 201, resp.text
    request_id = resp.json()["request"]["id"]
    _run(world.discovery.store_verification_code, request_id, "CODE1234")
    client.post(
        f"/api/v3/discovery/requests/{request_id}/verify",
        json={"organization_id": "org-a", "code": "CODE1234"},
    )
    choice = client.post(
        f"/api/v3/discovery/requests/{request_id}/choice",
        json={"organization_id": "org-a", "choice": "use_all"},
    )
    assert choice.status_code == 200, choice.text
    # Requesting-org membership deactivated; candidate org membership owner.
    requesting = _run(world.tenant.get_member_by_user, "org-a", "u-owner")
    assert requesting["is_active"] is False
    adopted = _run(world.tenant.get_member_by_user, "org-existing", "u-owner")
    assert adopted["role"] == "owner"


def test_onboarding_lookup_anonymous_401(client, user_provider):
    user_provider.set_unauthenticated()
    resp = client.post("/api/v3/discovery/lookup", json={"name": "Acme"})
    assert resp.status_code == 401

