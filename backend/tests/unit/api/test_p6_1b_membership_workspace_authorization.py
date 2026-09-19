"""P6-1B — Consultant membership, team & workspace authorization.

The canonical Layer-2 chain is enforced server-side:
identity -> ACTIVE consultant_firm_members membership -> the single distinct
firm (firm profile must exist and be active) -> permissions/client grants for
that firm only. These tests cover the negative and positive boundaries in the
P6-1B brief (CONSULT-SEC-001..009). In-memory; no database access.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from auth import AuthUser
from domain.billing import BillingPlan, Subscription
from services.billing import BillingService
from tests.unit.api.fakes import consultant_user, member_user


def _no_org_user(user_id: str = "u-cust", email: str = "cust@customer.test") -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email=email,
        role="user",
        role_name="user",
        is_active=True,
    )


def _seed_firm(
    world,
    user_id="u-cons",
    firm="firm-1",
    company="Acme Consultants",
    *,
    role="manager",
    is_active=True,
    profile_active=True,
    can_manage_clients=False,
    can_upload_documents=False,
    can_generate_reports=False,
    can_manage_team=True,
):
    world.consultants.seed_profile(firm, user_id, company, is_active=profile_active)
    world.consultants.seed_firm_member(
        firm,
        user_id,
        role=role,
        is_active=is_active,
        can_manage_clients=can_manage_clients,
        can_upload_documents=can_upload_documents,
        can_generate_reports=can_generate_reports,
        can_manage_team=can_manage_team,
    )
    return consultant_user(user_id, "cons@example.test")


def _run(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


# ---------------------------------------------------------------------------
# Workspace / membership boundary (Layer 1 + 2)
# ---------------------------------------------------------------------------


def test_unauthenticated_consultant_workspace_denied(client, user_provider) -> None:
    user_provider.set_unauthenticated()
    assert client.get("/api/v3/consultants/me").status_code == 401


def test_ordinary_customer_cannot_access_consultant_workspace(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/consultants/me").status_code == 403
    assert client.get("/api/v3/consultants/me/clients").status_code == 403


def test_profile_without_membership_denied(client, world, user_provider) -> None:
    """A consultant profile alone (no firm-membership row) grants no workspace."""
    world.consultants.seed_profile("firm-solo", "u-solo", "Solo Consultancy")
    user_provider.set_user(consultant_user("u-solo", "solo@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 403


def test_inactive_membership_denied(client, world, user_provider) -> None:
    _seed_firm(world, user_id="u-cons", is_active=False)
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 403


def test_inactive_firm_profile_denied(client, world, user_provider) -> None:
    _seed_firm(world, user_id="u-cons", profile_active=False)
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 403


def test_active_member_workspace_allowed_with_membership_state(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    resp = client.get("/api/v3/consultants/me")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    membership = body["membership"]
    assert membership["is_active"] is True
    assert membership["firm_id"] == "firm-1"
    assert membership["role"] == "manager"
    assert membership["source"] == "consultant_firm_members"
    assert body["entitlement_scope"]["bound_organization_id"] is None
    assert body["entitlement_scope"]["consultant_capability_required_for_workspace"] is False


def test_revoked_membership_denied_on_fresh_evaluation(client, world, user_provider) -> None:
    _seed_firm(world, user_id="u-cons")
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 200
    member_row = _run(world.consultants.get_firm_member_by_user, "firm-1", "u-cons")
    _run(world.consultants.set_firm_member_active, "firm-1", member_row.id, False)
    # A stale client "is consultant" state cannot survive: fresh server-side
    # evaluation denies.
    assert client.get("/api/v3/consultants/me").status_code == 403


def test_multiple_active_firms_ambiguous_denied(client, world, user_provider) -> None:
    """More than one distinct active firm is ambiguous -> denied, not guessed."""
    _seed_firm(world, user_id="u-cons")
    world.consultants.seed_profile("firm-2", "u-owner-2", "Second Firm")
    world.consultants.seed_firm_member("firm-2", "u-cons", role="consultant")
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 403


# ---------------------------------------------------------------------------
# Team / firm administration (Layer 4 permission gating)
# ---------------------------------------------------------------------------


def test_add_member_requires_manage_team(client, world, user_provider) -> None:
    _seed_firm(world, user_id="u-limited", can_manage_team=False)
    user_provider.set_user(consultant_user("u-limited", "limited@example.test"))
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-new", "role": "consultant"},
    )
    assert resp.status_code == 403, resp.text


def test_admin_can_add_member_with_safe_defaults(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons", can_manage_team=True)
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-new", "role": "Consultant"},
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    # The real permission flags stay FALSE — membership alone grants nothing.
    assert created["role"] == "consultant"
    assert created["can_manage_clients"] is False
    assert created["can_upload_documents"] is False
    assert created["can_generate_reports"] is False
    assert created["can_manage_team"] is False
    row = _run(world.consultants.get_firm_member_by_user, "firm-1", "u-new")
    assert row is not None and row.user_id == "u-new"


def test_add_member_rejects_unknown_role(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-new", "role": "supreme-admin"},
    )
    assert resp.status_code == 422, resp.text


def test_add_member_duplicate_rejected(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    world.consultants.seed_firm_member("firm-1", "u-exists", role="consultant")
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-exists", "role": "consultant"},
    )
    assert resp.status_code == 409, resp.text


def test_add_member_self_rejected(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-cons", "role": "manager"},
    )
    assert resp.status_code == 422, resp.text


def test_forged_permission_flags_ignored_on_add(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/team",
        json={
            "user_id": "u-new",
            "role": "consultant",
            "can_manage_clients": True,
            "can_manage_team": True,
            "permissions": {"everything": True},
        },
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["can_manage_clients"] is False
    assert created["can_manage_team"] is False


def test_cross_firm_member_admin_action_denied(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    world.consultants.seed_firm_member("firm-2", "u-other", role="consultant")
    user_provider.set_user(user)
    other = next(
        m for m in world.consultants._members
        if m.firm_id == "firm-2" and m.user_id == "u-other"
    )
    resp = client.post(f"/api/v3/consultants/me/team/{other.id}/deactivate")
    assert resp.status_code == 404, resp.text



# ---------------------------------------------------------------------------
# Client-resource boundary (Layer 5) — membership/capability never grants it
# ---------------------------------------------------------------------------


def test_active_grant_allows_client_resource_access(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD")
    user_provider.set_user(user)
    resp = client.get("/api/v3/consultants/clients/client-a/context")
    assert resp.status_code == 200, resp.text


def test_membership_alone_never_grants_client_access(client, world, user_provider) -> None:
    """Active membership with NO active grant cannot reach client data."""
    user = _seed_firm(world, user_id="u-cons")
    # Same firm, but the ONLY grant is inactive -> no client-resource access.
    world.consultants.seed_client("client-idle", "firm-1", "org-a", "Idle Ltd", status="inactive")
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-idle/documents").status_code == 403
    # A grant belonging to ANOTHER firm is equally unreachable.
    world.consultants.seed_client("client-other", "firm-2", "org-c", "Other Ltd")
    assert client.get("/api/v3/consultants/clients/client-other/documents").status_code == 403


def test_forged_firm_or_org_id_cannot_bypass(client, world, user_provider) -> None:
    """Consultant-supplied ids never select a firm; server state decides."""
    user = _seed_firm(world, user_id="u-cons")
    world.consultants.seed_client("client-other", "firm-2", "org-c", "Other Ltd")
    user_provider.set_user(user)
    # client-other belongs to firm-2 — accessing it via its id is denied even
    # though the caller can send any id.
    resp = client.get("/api/v3/consultants/clients/client-other/documents")
    assert resp.status_code == 403, resp.text


def test_unknown_client_id_not_found(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-ghost/context").status_code == 404


def _first_get_route(client, prefix: str):
    """First GET route under ``prefix``, taken from the app's OWN OpenAPI document.

    ``app.routes`` holds framework-internal lazy wrappers in the installed FastAPI version
    (``_IncludedRouter``), so the previous scan of ``app.routes`` found no ``APIRoute`` for
    these prefixes and the two boundary assertions below failed VACUOUSLY ("expected a GET
    commercial (staff) route") instead of proving anything. The OpenAPI document is the
    stable, framework-independent source of the app's routing table.
    """
    document = client.app.openapi() or {}
    candidates = [
        path
        for path, operations in (document.get("paths") or {}).items()
        if path.startswith(prefix) and "get" in operations
    ]
    parameterless = [path for path in candidates if "{" not in path]
    if parameterless:
        return parameterless[0]
    return candidates[0] if candidates else None


def test_consultant_cannot_reach_operations_surface(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    # /api/v3/commercial/* is internal staff (can_manage_billing) only.
    route = _first_get_route(client, "/api/v3/commercial/")
    assert route, "expected a GET commercial (staff) route"
    resp = client.get(route)
    assert resp.status_code == 403, resp.text


def test_consultant_cannot_reach_pe_surface(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-cons")
    user_provider.set_user(user)
    # /api/v3/pe/* is Processing-Entity staff only.
    route = _first_get_route(client, "/api/v3/pe/")
    if route is None:  # pragma: no cover — PE router absent
        raise AssertionError("expected at least one GET /api/v3/pe/ route")
    resp = client.get(route)
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Capability layer participation (Layer 3 — org-scoped, distinct from membership)
# ---------------------------------------------------------------------------


def _seed_plan_with_consultant_feature(world) -> None:
    _run(
        world.billing_plans.create,
        BillingPlan(
            id=str(uuid.uuid4()),
            plan_code="consultant-plus",
            name="Consultant Plus",
            price=199,
            currency="USD",
            included_credits=0,
            version=1,
            is_active=True,
            features={
                "consultant": {
                    "enabled": True,
                    "client_capacity": 5,
                    "team_member_limit": 10,
                    "white_label": True,
                    "workspace": True,
                }
            },
            effective_from=datetime.now(timezone.utc),
        ),
        created_by=None,
    )


def _activate_org_consultant_plan(world, org_id: str) -> None:
    _run(
        world.billing_subscriptions.upsert_active,
        Subscription(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            plan_code="consultant-plus",
            plan_version=1,
            billing_mode="CREDIT",
            lifecycle_status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
            idempotency_key="p6-1b-activate",
        ),
        created_by="admin-1",
    )


def test_org_with_capability_and_member_resolves_both_layers(world) -> None:
    """Capability (org subscription) and membership are independent layers."""
    _seed_plan_with_consultant_feature(world)
    _activate_org_consultant_plan(world, "org-a")
    cap = _run(BillingService(world.bundle()).consultant_capability, "org-a")
    assert cap["entitled"] is True
    # Membership layer (same user) is unaffected by capability state.
    world.consultants.seed_profile("firm-1", "u-cons", "Acme")
    world.consultants.seed_firm_member("firm-1", "u-cons", role="manager")
    memberships = _run(world.consultants.get_active_memberships_by_user, "u-cons")
    assert len(memberships) == 1
    assert memberships[0].firm_id == "firm-1"
    # Capability never self-creates a client grant for the org.
    assert _run(world.consultants.get_client_by_org, "firm-1", "org-a") is None



# ---------------------------------------------------------------------------
# Workstream E — the cross-SURFACE boundary (entity routing, API level)
# ---------------------------------------------------------------------------
# Required verification: the PE path, the consultant path, the client path and the
# internal path must not be interchangeable, and unauthorised direct navigation must be
# refused SERVER-side (the UI is never the security boundary). The guards below are the
# same ones the routes above them use; each caller here is a REAL AuthUser.

from domain.entity import ProcessingEntity  # noqa: E402
from domain.staff import StaffProfile, StaffRole  # noqa: E402
from tests.unit.api.fakes import entity_operator_user, staff_user  # noqa: E402


def _seed_entity_world(world) -> None:
    """One active entity with an operator (PE domain) plus a suspended one."""
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    _run(world.entities.save,
         ProcessingEntity(id="entity-1", name="Processing Entity A", status="active"))
    _run(world.entities.save,
         ProcessingEntity(id="entity-2", name="Processing Entity B", status="suspended"))
    world.staff.seed_profile(StaffProfile(
        id="sp-ent1", user_id="u-ent1", first_name="Ent", last_name="A",
        email="enta@entity.test", role_id="role-operator", entity_id="entity-1",
    ))
    world.staff.seed_profile(StaffProfile(
        id="sp-internal", user_id="u-internal", first_name="Internal", last_name="Op",
        email="internal@carbontally.test", role_id="role-operator", entity_id=None,
    ))


def test_internal_staff_are_denied_on_the_pe_surface(client, world, user_provider) -> None:
    """`api/pe_auth.py`: internal staff (entity_id IS NULL) belong to /ops, not /pe."""
    _seed_entity_world(world)
    user_provider.set_user(staff_user("u-internal", email="internal@carbontally.test"))
    assert client.get("/api/v3/pe/me").status_code == 403


def test_pe_staff_can_reach_their_own_pe_surface(client, world, user_provider) -> None:
    """The PE path itself works end to end for entity staff (not merely denied elsewhere)."""
    _seed_entity_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get("/api/v3/pe/me")
    assert response.status_code == 200, response.text
    assert response.json()["entity"]["id"] == "entity-1"
    assert "pe_manager" in response.json()["role"]["key"] or \
        response.json()["role"]["key"] in ("operator", "reviewer", "qc_specialist")


def test_pe_staff_are_denied_on_the_internal_commercial_surface(
    client, world, user_provider
) -> None:
    """The PE domain never grants CarbonTally-internal privileges (PE-ROLE-001)."""
    _seed_entity_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    route = _first_get_route(client, "/api/v3/commercial/")
    assert route, "expected a GET commercial (staff) route"
    assert client.get(route).status_code == 403


def test_pe_staff_are_denied_on_the_internal_operations_surface(
    client, world, user_provider
) -> None:
    """An internal-only operations queue is refused to entity staff (not merely hidden)."""
    _seed_entity_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    route = _first_get_route(client, "/api/v3/qc/")
    assert route, "expected a GET qc (internal staff) route"
    assert client.get(route).status_code == 403


def test_a_pe_staff_member_of_a_suspended_entity_is_denied(
    client, world, user_provider
) -> None:
    """Entity status is enforced, not assumed: a suspended entity has no PE workspace."""
    _seed_entity_world(world)
    user_provider.set_user(entity_operator_user("entity-2", "u-ent2"))
    assert client.get("/api/v3/pe/me").status_code == 403


def test_a_pe_staff_identity_cannot_name_another_entity(
    client, world, user_provider
) -> None:
    """Entity isolation: the entity is resolved from the identity, never from a parameter."""
    _seed_entity_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get("/api/v3/pe/issues", params={"entity_id": "entity-2"})
    assert response.status_code in (200, 403), response.text
    if response.status_code == 200:
        # every returned row must belong to the caller's own entity
        for issue in response.json().get("issues", []):
            assert issue.get("entity_id") in (None, "entity-1")


def test_a_customer_cannot_reach_the_pe_surface(client, world, user_provider) -> None:
    _seed_entity_world(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/pe/me").status_code == 403


def test_a_consultant_cannot_reach_the_pe_surface(client, world, user_provider) -> None:
    _seed_entity_world(world)
    user_provider.set_user(_seed_firm(world, user_id="u-cons-pe"))
    assert client.get("/api/v3/pe/me").status_code == 403


def test_an_unauthenticated_caller_is_refused_on_the_pe_surface(
    client, world, user_provider
) -> None:
    user_provider.set_unauthenticated()
    assert client.get("/api/v3/pe/me").status_code == 401


def test_the_pe_surface_is_not_readable_across_entities(
    client, world, user_provider
) -> None:
    """Cross-entity isolation on the PE work read (entity A must not see entity B)."""
    _seed_entity_world(world)
    _run(world.manual_extraction.create_batch, "org-a", "Entity B work", created_by="u-mgr")
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get("/api/v3/pe/issues")
    assert response.status_code == 200
    assert response.json().get("issues", []) == []      # entity B's work is invisible

