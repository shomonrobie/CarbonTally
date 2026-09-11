"""P6-1C — Consultant Engagement Confirmation for pre-existing organisations.

Authorization model under test:

  * A Consultant can never acquire client access to an ALREADY-EXISTING
    CarbonTally organisation by naming it (``POST /me/clients`` now creates a
    PENDING ``engagement_request`` — never an instant ``active`` grant).
  * Customer acceptance (org owner/admin) is the ONLY path
    ``pending -> active``; rejection moves ``pending -> rejected`` and grants
    nothing.
  * Firm-side lifecycle moves are origin-aware: legacy/consultant-CREATED
    relationships keep the ratified D19 firm lifecycle; ``engagement_request``
    rows may be withdrawn (-> ended), re-requested (rejected/ended -> pending)
    and suspended/ended once live — but the firm can never activate its own
    pending engagement or manufacture pending/rejected on created customers.
  * Organisation/role/engagement boundaries are enforced server-side on both
    the consultant and customer surfaces (every negative case below is a
    hard 403/404/409 — not a hidden button).
"""
from __future__ import annotations

from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_admin_user,
    org_owner_user,
)
from tests.unit.api.route_paths import flatten_router_paths

CONSULTANTS = "/api/v3/consultants"
ORGS = "/api/v3/organizations"

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/consultants/me/engagements",
    "/api/v3/organizations/{org_id}/consultant-engagements",
    "/api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept",
    "/api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/reject",
)


def test_p6_1c_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing P6-1C routes: {missing}"


def _seed_firm(world, user_id="u-p1", *, can_manage_clients=True):
    """A Consultant firm (firm-p1) with NO clients — every relationship in the
    tests is created through the engagement flow under test."""
    world.consultants.seed_profile("firm-p1", user_id, "P1 Advisory")
    world.consultants.seed_firm_member(
        "firm-p1",
        user_id,
        role="manager",
        can_manage_clients=can_manage_clients,
        can_upload_documents=True,
        can_generate_reports=True,
        can_manage_team=True,
    )
    return consultant_user(user_id, "p1@example.test")


def _seed_existing_org(world, org_id="org-p6", *, customer_type=None):
    """An ALREADY-EXISTING (non-consultant-owned) organisation — Case B."""
    return world.organizations.seed_org(
        org_id, name="P6 Client Org", customer_type=customer_type
    )


def _seed_pending_engagement(world, org_id="org-p6", engagement_id="p6-eng-1"):
    _seed_existing_org(world, org_id)
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        engagement_id, "firm-p1", org_id, "P6 Client Org",
        status="pending", relationship_origin="engagement_request",
    )


# ---------------------------------------------------------------------------
# 1. Request creation — existing organisation never grants instant access
# ---------------------------------------------------------------------------


def test_request_requires_manage_clients_permission(client, world, user_provider) -> None:
    _seed_existing_org(world)
    user = _seed_firm(world, can_manage_clients=False)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "P6 Client Org"},
    )
    assert response.status_code == 403


def test_request_to_existing_org_creates_pending_engagement(client, world, user_provider) -> None:
    _seed_existing_org(world)
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "P6 Client Org"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["organization_id"] == "org-p6"
    assert body["status"] == "pending"
    assert body["relationship_origin"] == "engagement_request"
    assert body["engagement_requested_at"] is not None
    assert body["engagement_decided_by"] is None


def test_request_to_nonexistent_org_is_404(client, world, user_provider) -> None:
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-does-not-exist", "client_name": "Ghost"},
    )
    assert response.status_code == 404


def test_request_duplicate_active_relationship_is_409(client, world, user_provider) -> None:
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client("p6-existing", "firm-p1", "org-p6", "P6 Client Org")
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "again"},
    )
    assert response.status_code == 409


def test_request_duplicate_pending_is_409(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "again"},
    )
    assert response.status_code == 409


def test_rejected_engagement_can_be_rerquested(client, world, user_provider) -> None:
    _seed_existing_org(world)
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-rej", "firm-p1", "org-p6", "P6 Client Org",
        status="rejected", relationship_origin="engagement_request",
    )
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "P6 Client Org"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_request_to_internal_org_type_denied(client, world, user_provider) -> None:
    _seed_existing_org(world, customer_type="internal")
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.post(
        f"{CONSULTANTS}/me/clients",
        json={"organization_id": "org-p6", "client_name": "P6 Client Org"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 2. Firm-side restrictions (origin-aware lifecycle policy)
# ---------------------------------------------------------------------------


def test_firm_cannot_activate_own_pending_engagement(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.put(
        f"{CONSULTANTS}/clients/p6-eng-1", json={"status": "active"}
    )
    assert response.status_code == 403


def test_firm_cannot_activate_own_rejected_engagement(client, world, user_provider) -> None:
    _seed_existing_org(world)
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-rej2", "firm-p1", "org-p6", "P6 Client Org",
        status="rejected", relationship_origin="engagement_request",
    )
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.put(
        f"{CONSULTANTS}/clients/p6-rej2", json={"status": "active"}
    )
    assert response.status_code == 403


def test_firm_may_withdraw_pending_request(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.put(
        f"{CONSULTANTS}/clients/p6-eng-1", json={"status": "ended"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ended"


def test_firm_cannot_manufacture_pending_on_created_customer(
    client, world, user_provider
) -> None:
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-created", "firm-p1", "org-p6", "P6 Client Org"
    )  # origin defaults to consultant_created_customer
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.put(
        f"{CONSULTANTS}/clients/p6-created", json={"status": "pending"}
    )
    assert response.status_code == 403


def test_created_customer_keeps_d19_firm_lifecycle(client, world, user_provider) -> None:
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-created2", "firm-p1", "org-p6", "P6 Client Org"
    )
    user = _seed_firm(world)
    user_provider.set_user(user)
    response = client.put(
        f"{CONSULTANTS}/clients/p6-created2", json={"status": "suspended"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


def test_firm_engagements_list_only_engagement_request_rows(
    client, world, user_provider
) -> None:
    _seed_pending_engagement(world)
    world.consultants.seed_client(
        "p6-created3", "firm-p1", "org-x", "Created Org X"
    )
    user = _seed_firm(world)
    user_provider.set_user(user)
    engagements = client.get(f"{CONSULTANTS}/me/engagements").json()["engagements"]
    assert [e["id"] for e in engagements] == ["p6-eng-1"]


# ---------------------------------------------------------------------------
# 3. Customer side — list/accept/reject (org owner + admin authority)
# ---------------------------------------------------------------------------


def test_customer_owner_lists_pending_engagements(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(org_owner_user("org-p6", "u-own", "owner@client.test"))
    response = client.get(f"{ORGS}/org-p6/consultant-engagements")
    assert response.status_code == 200
    engagements = response.json()["engagements"]
    assert len(engagements) == 1
    assert engagements[0]["id"] == "p6-eng-1"
    assert engagements[0]["firm_name"] == "P1 Advisory"
    assert engagements[0]["status"] == "pending"


def test_customer_member_cannot_list_engagements(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(member_user("org-p6", "u-mem", "member@client.test"))
    assert client.get(f"{ORGS}/org-p6/consultant-engagements").status_code == 403


def test_other_org_admin_cannot_list_engagements(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(org_admin_user("org-other", "u-oth", "other@test"))
    assert client.get(f"{ORGS}/org-p6/consultant-engagements").status_code == 403


def test_customer_owner_accept_activates_engagement(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    # Before acceptance the engagement grants NO consultant access.
    firm_user = _seed_firm(world)
    user_provider.set_user(firm_user)
    dashboard = client.get(f"{CONSULTANTS}/me/dashboard").json()
    assert dashboard["active_client_count"] == 0
    assert dashboard["client_count"] == 1  # the pending row is visible but inert

    user_provider.set_user(org_owner_user("org-p6", "u-own", "owner@client.test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-eng-1/accept")
    assert response.status_code == 200
    body = response.json()["engagement"]
    assert body["status"] == "active"
    assert body["engagement_decided_by"] == "u-own"
    assert body["engagement_decided_at"] is not None

    # Acceptance is server-state: the consultant now has an ACTIVE client.
    user_provider.set_user(firm_user)
    dashboard = client.get(f"{CONSULTANTS}/me/dashboard").json()
    assert dashboard["active_client_count"] == 1
    assert dashboard["clients_by_status"]["active"] == 1


def test_customer_admin_accept_activates_engagement(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(org_admin_user("org-p6", "u-adm", "admin@client.test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-eng-1/accept")
    assert response.status_code == 200
    assert response.json()["engagement"]["status"] == "active"
    assert response.json()["engagement"]["engagement_decided_by"] == "u-adm"


def test_customer_member_cannot_accept(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(member_user("org-p6", "u-mem", "member@client.test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-eng-1/accept")
    assert response.status_code == 403


def test_other_org_owner_cannot_accept(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(org_owner_user("org-other", "u-oth", "other@test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-eng-1/accept")
    assert response.status_code == 403


def test_accept_non_pending_engagement_is_409(client, world, user_provider) -> None:
    _seed_existing_org(world)
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-live", "firm-p1", "org-p6", "P6 Client Org",
        status="active", relationship_origin="engagement_request",
    )
    user_provider.set_user(org_owner_user("org-p6", "u-own", "owner@client.test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-live/accept")
    assert response.status_code == 409


def test_accept_unknown_engagement_is_404(client, world, user_provider) -> None:
    _seed_existing_org(world)
    user_provider.set_user(org_owner_user("org-p6", "u-own", "owner@client.test"))
    response = client.post(
        f"{ORGS}/org-p6/consultant-engagements/p6-missing/accept"
    )
    assert response.status_code == 404


def test_accept_engagement_of_other_org_is_denied(client, world, user_provider) -> None:
    # The engagement exists, but it targets org-other — org-p6 may not touch it.
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-cross", "firm-p1", "org-other", "Other Org",
        status="pending", relationship_origin="engagement_request",
    )
    user_provider.set_user(org_owner_user("org-p6", "u-own", "owner@client.test"))
    response = client.post(f"{ORGS}/org-p6/consultant-engagements/p6-cross/accept")
    assert response.status_code == 403


def test_firm_can_suspend_and_reactivate_live_engagement(
    client, world, user_provider
) -> None:
    # Once accepted (active), the firm regains the normal D19 lifecycle tools.
    world.consultants.seed_profile("firm-p1", "u-p1", "P1 Advisory")
    world.consultants.seed_client(
        "p6-live2", "firm-p1", "org-p6", "P6 Client Org",
        status="active", relationship_origin="engagement_request",
    )
    user = _seed_firm(world)
    user_provider.set_user(user)
    suspended = client.put(
        f"{CONSULTANTS}/clients/p6-live2", json={"status": "suspended"}
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"
    restored = client.put(
        f"{CONSULTANTS}/clients/p6-live2", json={"status": "active"}
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"


# ---------------------------------------------------------------------------
# 4. Domain policy (pure) — the canonical transition rules
# ---------------------------------------------------------------------------


def test_domain_engagement_policy_customer_side() -> None:
    from domain.partners import can_transition_consultant_engagement

    assert can_transition_consultant_engagement(
        "pending", "active", actor_side="customer", origin="engagement_request"
    )
    assert can_transition_consultant_engagement(
        "pending", "rejected", actor_side="customer", origin="engagement_request"
    )
    assert not can_transition_consultant_engagement(
        "active", "rejected", actor_side="customer", origin="engagement_request"
    )
    assert not can_transition_consultant_engagement(
        "rejected", "active", actor_side="customer", origin="engagement_request"
    )
    assert not can_transition_consultant_engagement(
        "pending", "active", actor_side="consultant", origin="engagement_request"
    )
    # Case A (consultant-created customer) keeps the ratified D19 lifecycle:
    # the firm may restore a suspended relationship without a new acceptance.
    assert can_transition_consultant_engagement(
        "suspended", "active", actor_side="consultant",
        origin="consultant_created_customer",
    )


def test_domain_engagement_policy_consultant_side() -> None:
    from domain.partners import can_transition_consultant_engagement

    origin = "engagement_request"
    # Withdraw pending / re-request rejected+ended / normal live lifecycle.
    assert can_transition_consultant_engagement(
        "pending", "ended", actor_side="consultant", origin=origin)
    assert can_transition_consultant_engagement(
        "rejected", "pending", actor_side="consultant", origin=origin)
    assert can_transition_consultant_engagement(
        "ended", "pending", actor_side="consultant", origin=origin)
    assert can_transition_consultant_engagement(
        "active", "suspended", actor_side="consultant", origin=origin)
    assert can_transition_consultant_engagement(
        "suspended", "active", actor_side="consultant", origin=origin)
    # Never consultant-activated from pending/rejected.
    assert not can_transition_consultant_engagement(
        "pending", "active", actor_side="consultant", origin=origin)
    assert not can_transition_consultant_engagement(
        "rejected", "active", actor_side="consultant", origin=origin)
    # No-op moves are not meaningful transitions.
    assert not can_transition_consultant_engagement(
        "pending", "pending", actor_side="consultant", origin=origin)



