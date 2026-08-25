"""D20 scope-aware authorization hardening (APPROVED 2026-08-20) — unit tests.

Covers the scope-first authorization boundary at the dependency level
(``require_admin`` / ``require_role`` / ``require_org_admin`` /
``ensure_org_access`` / ``ensure_consultant_org_access``) and at the API level
(business endpoints, consultant client access, legacy-roles independence).

Threat scenarios exercised:
  A — internal staff + admin role             → ALLOWED (internal admin)
  B — entity staff + admin role name          → entity-scoped authority only
  C — entity staff → arbitrary customer org   → DENIED
  D — org admin within/outside their org      → ALLOWED / DENIED
  E — consultant ACTIVE client                → ALLOWED per permissions
  F — consultant INACTIVE/REVOKED client      → DENIED (D15)
  G — consultant cross-org                    → DENIED
  H — legacy `roles` record must not grant staff authority
  I — unbound user / entity staff → /api/v2/business/* org access → DENIED
  J — entity staff never passes legacy admin guards (role-name matching)
  K — entity staff never passes the customer-communication guard
  L — entity staff never passes the consultant surface

No database access — all in-memory fakes.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.consultant_auth import ensure_consultant_org_access
from api.dependencies import ensure_org_access
from auth import AuthUser, require_admin, require_org_admin, require_role
from domain.staff import StaffProfile, StaffRole

from tests.unit.api.fakes import consultant_user

CALCULATE_PAYLOAD = {
    "organization_id": "org-a",
    "factor_id": "factor-defra-gas",
    "quantity": "1000",
    "quantity_unit": "kWh",
    "date": "2025-06-01",
    "reporting_year": 2025,
    "activity": "Natural gas consumption",
    "activity_type": "Natural gas",
}


# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------


def _internal_admin() -> AuthUser:
    """CarbonTally internal staff with an ``admin``-named role."""
    return AuthUser(
        user_id="u-int-admin",
        email="int-admin@carbontally.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        entity_id=None,
        is_org_member=False,
        is_admin=True,
    )


def _entity_admin() -> AuthUser:
    """Processing Entity staff with an ``admin``-named role (dangerous)."""
    return AuthUser(
        user_id="u-ent-admin",
        email="ent-admin@entity.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        entity_id="entity-a",
        is_org_member=False,
        is_admin=False,
    )


def _entity_operator() -> AuthUser:
    """Processing Entity staff with a non-admin entity role."""
    return AuthUser(
        user_id="u-ent-op",
        email="ent-op@entity.test",
        role="entity_staff",
        role_name="entity_operator",
        is_staff=True,
        entity_id="entity-a",
        is_org_member=False,
    )


def _unbound_user() -> AuthUser:
    """An authenticated user with no organisation and no staff profile."""
    return AuthUser(
        user_id="u-none",
        email="nobody@example.test",
        role="user",
        role_name="user",
        is_staff=False,
        is_org_member=False,
    )


def _org_admin(org_id: str) -> AuthUser:
    return AuthUser(
        user_id="u-orgadmin",
        email="orgadmin@example.test",
        role="org_admin",
        role_name="org_admin",
        is_org_member=True,
        organization_id=org_id,
    )


def _internal_staff_plain() -> AuthUser:
    """Internal staff whose staff_roles record grants nothing."""
    return AuthUser(
        user_id="u-h",
        email="h@carbontally.test",
        role="staff",
        role_name="operator",
        is_staff=True,
        entity_id=None,
        is_org_member=False,
        permissions={},
    )


def _seed_consultant(world) -> AuthUser:
    """Seed a consultant firm with an active client, an inactive client and a
    cross-firm client."""
    world.consultants.seed_profile("firm-1", "u-cons", "Acme")
    world.consultants.seed_firm_member(
        "firm-1",
        "u-cons",
        role="manager",
        can_manage_clients=True,
        can_upload_documents=True,
        can_generate_reports=True,
    )
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD")  # active
    world.consultants.seed_client(
        "client-b", "firm-1", "org-b", "Example Manufacturing", status="inactive"
    )
    world.consultants.seed_client("client-c", "firm-2", "org-c", "Other Retail")
    return consultant_user("u-cons", "cons@example.test")


# ---------------------------------------------------------------------------
# A — Internal staff + admin role
# ---------------------------------------------------------------------------


async def test_a_internal_admin_holds_internal_admin_authority() -> None:
    user = _internal_admin()
    assert user.is_internal_staff is True
    assert user.is_entity_staff is False
    assert user.is_admin is True
    assert await require_admin()(user) is user
    assert await require_role(["admin", "staff"])(user) is user


# ---------------------------------------------------------------------------
# B — Entity staff + admin role name → entity-scoped authority only
# ---------------------------------------------------------------------------


async def test_b_entity_staff_admin_role_is_not_internal_admin() -> None:
    user = _entity_admin()
    assert user.is_entity_staff is True
    assert user.is_internal_staff is False
    # The dangerous flag: an entity staff profile with an admin-named role.
    assert user.is_admin is False
    with pytest.raises(HTTPException) as exc:
        await require_admin()(user)
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc2:
        await require_role(["admin", "staff"])(user)
    assert exc2.value.status_code == 403


# ---------------------------------------------------------------------------
# C — Entity staff → arbitrary customer organisation → DENIED
# ---------------------------------------------------------------------------


def test_c_ensure_org_access_denies_entity_staff() -> None:
    with pytest.raises(HTTPException) as exc:
        ensure_org_access(_entity_admin(), "org-a")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# D — Customer organisation admin: allowed inside, denied outside
# ---------------------------------------------------------------------------


def test_d_org_admin_scoped_to_own_organisation() -> None:
    user = _org_admin("org-a")
    ensure_org_access(user, "org-a")  # must not raise
    with pytest.raises(HTTPException) as exc:
        ensure_org_access(user, "org-b")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# I — No arbitrary organisation access through ensure_org_access
# ---------------------------------------------------------------------------


def test_i_unbound_non_staff_denied_any_organisation() -> None:
    with pytest.raises(HTTPException) as exc:
        ensure_org_access(_unbound_user(), "org-a")
    assert exc.value.status_code == 403


def test_i_business_calculate_denies_entity_staff(client, user_provider) -> None:
    user_provider.set_user(_entity_admin())
    assert client.post("/api/v2/calculate", json=CALCULATE_PAYLOAD).status_code == 403


def test_i_business_calculate_denies_unbound_non_staff(client, user_provider) -> None:
    user_provider.set_user(_unbound_user())
    assert client.post("/api/v2/calculate", json=CALCULATE_PAYLOAD).status_code == 403


def test_i_business_calculate_allows_internal_staff(client) -> None:
    # The default fixture user (admin_user) is CarbonTally internal staff.
    assert client.post("/api/v2/calculate", json=CALCULATE_PAYLOAD).status_code == 200


# ---------------------------------------------------------------------------
# J — Entity staff never pass legacy admin guards (role-name matching)
# ---------------------------------------------------------------------------


async def test_j_entity_staff_never_passes_global_admin_path() -> None:
    with pytest.raises(HTTPException) as exc:
        await require_org_admin()(_entity_admin())
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc2:
        await require_org_admin()(_entity_operator())
    assert exc2.value.status_code == 403


# ---------------------------------------------------------------------------
# E / F / G — Consultant client access (D15)
# ---------------------------------------------------------------------------


def test_e_consultant_active_client_allowed(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert (
        client.get("/api/v3/consultants/clients/client-a/documents").status_code
        == 200
    )


def test_f_consultant_inactive_client_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    # D15: relationship ended → data access ends.
    assert (
        client.get("/api/v3/consultants/clients/client-b/documents").status_code
        == 403
    )
    # The firm may still manage its own grant row (reactivation).
    assert (
        client.put(
            "/api/v3/consultants/clients/client-b", json={"status": "active"}
        ).status_code
        == 200
    )


def test_g_consultant_cross_firm_client_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert (
        client.get("/api/v3/consultants/clients/client-c/documents").status_code
        == 403
    )


async def test_f_ensure_consultant_org_access_denies_inactive(world) -> None:
    from api.consultant_auth import require_consultant

    user = _seed_consultant(world)
    context = await require_consultant(current_user=user, repos=world.bundle())
    assert context is not None
    await ensure_consultant_org_access(user, world.bundle(), "org-a")  # active ok
    with pytest.raises(HTTPException) as exc:
        await ensure_consultant_org_access(user, world.bundle(), "org-b")  # inactive
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# H — Legacy `roles` must never grant CarbonTally staff authority
# ---------------------------------------------------------------------------


def test_h_legacy_roles_record_does_not_grant_staff_authority(
    client, world, user_provider
) -> None:
    # A legacy `roles` row grants can_process / can_view_all...
    world.roles.seed(
        {
            "id": "r-legacy-admin",
            "name": "admin",
            "permissions": {"can_process": True, "can_view_all": True},
        }
    )
    # ...but the staff profile's staff_roles record grants nothing.
    world.staff.seed_role(StaffRole(id="role-h", name="operator", permissions={}))
    world.staff.seed_profile(
        StaffProfile(
            id="sp-h",
            user_id="u-h",
            first_name="H",
            last_name="H",
            email="h@carbontally.test",
            role_id="role-h",
            entity_id=None,
            is_active=True,
        )
    )
    user_provider.set_user(_internal_staff_plain())
    # The can_process-gated ops surface is denied despite the roles row.
    assert client.get("/api/v3/ops/queues/operator").status_code == 403
    # Staff permissions are resolved from staff_roles, not the roles table.
    body = client.get("/api/v3/ops/me").json()
    assert body["permissions"] == {}


# ---------------------------------------------------------------------------
# K / L — Entity staff have no customer/consultant communication authority
# ---------------------------------------------------------------------------


async def test_k_entity_staff_cannot_pass_customer_communication_guard() -> None:
    # The guard on the legacy customer-facing email endpoints and
    # customer_documents /staff/organize.
    with pytest.raises(HTTPException) as exc:
        await require_role(["admin", "staff"])(_entity_operator())
    assert exc.value.status_code == 403


def test_l_entity_staff_denied_consultant_surface(client, world, user_provider) -> None:
    from tests.unit.api.fakes import entity_operator_user

    user_provider.set_user(entity_operator_user("entity-a", "u-ent-op"))
    assert client.get("/api/v3/consultants/me").status_code == 403
