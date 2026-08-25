"""V3 customer administration (Phase 6) — route registration + API behaviour.

Covers the customer administration surface: organization profile/settings,
members, invitations, roles, suppliers, facilities, assets — org isolation,
role authorization, invalid IDs, and unauthorized access — against the
in-memory world.
"""
from __future__ import annotations

from api.v3_organizations import ORG_ROLES, validate_org_role
from tests.unit.api.fakes import member_user, org_admin_user, org_owner_user
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/organizations/{org_id}",
    "/api/v3/organizations/{org_id}/profile",
    "/api/v3/organizations/{org_id}/metadata",
    "/api/v3/organizations/{org_id}/members",
    "/api/v3/organizations/members/{member_id}",
    "/api/v3/organizations/{org_id}/roles",
    "/api/v3/organizations/{org_id}/invitations",
    "/api/v3/organizations/invitations/{invitation_id}",
    "/api/v3/organizations/{org_id}/facilities",
    "/api/v3/organizations/facilities/{facility_id}",
    "/api/v3/organizations/{org_id}/assets",
    "/api/v3/organizations/assets/{asset_id}",
    "/api/v3/suppliers",
)


def test_v3_customer_admin_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 customer-admin routes: {missing}"


def test_org_roles_match_schema_check() -> None:
    # The V3 customer role model is the organization_members.role CHECK set.
    assert ORG_ROLES == ("owner", "admin", "member", "viewer")


def test_validate_org_role_rejects_unknown() -> None:
    try:
        validate_org_role("superadmin")
        assert False, "expected HTTPException"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422


def test_validate_org_role_accepts_schema_roles() -> None:
    for role in ORG_ROLES:
        validate_org_role(role)  # must not raise


# ---------------------------------------------------------------------------
# Organization access + profile
# ---------------------------------------------------------------------------


def test_get_organization_profile_member(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/profile")
    assert response.status_code == 200
    org = response.json()["organization"]
    assert org["name"] == "Org A"
    assert org["country"] == "GB"
    assert org["is_active"] is True


def test_get_organization_profile_org_isolation(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/profile").status_code == 403


def test_get_organization_profile_nonexistent(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    # The API authorizes org access first (deny-before-reveal): a caller who is
    # not a member of the requested org receives 403, never a 404 existence leak.
    assert client.get("/api/v3/organizations/does-not-exist/profile").status_code == 403


def test_get_organization_profile_requires_org_member(client) -> None:
    # Default fixture user is staff (not an org member) → 403.
    assert client.get("/api/v3/organizations/org-a/profile").status_code == 403


def test_update_profile_admin(client, world, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/org-a/profile",
        json={"company_number": "12345678", "industry": "Manufacturing", "secr_enabled": True},
    )
    assert response.status_code == 200
    org = response.json()["organization"]
    assert org["company_number"] == "12345678"
    assert org["industry"] == "Manufacturing"
    assert org["secr_enabled"] is True
    assert org["id"] == "org-a"


def test_update_profile_requires_admin(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.put(
        "/api/v3/organizations/org-a/profile",
        json={"company_number": "12345678"},
    )
    assert response.status_code == 403


def test_update_profile_rejects_unknown_field(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/org-a/profile",
        json={"made_up_field": "nope"},
    )
    assert response.status_code == 422


def test_update_profile_empty_payload(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put("/api/v3/organizations/org-a/profile", json={})
    assert response.status_code == 422


def test_update_profile_org_isolation(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/org-b/profile",
        json={"company_number": "999"},
    )
    assert response.status_code == 403


def test_update_profile_nonexistent_org(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/does-not-exist/profile",
        json={"company_number": "999"},
    )
    # Deny-before-reveal: non-member org access returns 403 (see the GET test).
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Organization settings / metadata
# ---------------------------------------------------------------------------


def test_get_metadata_member(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/metadata")
    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["organization_id"] == "org-a"
    assert metadata["average_employees"] == 10  # seeded Org A fte_count


def test_get_metadata_org_isolation(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/metadata").status_code == 403


def test_update_metadata_admin(client, world, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/org-a/metadata",
        json={"total_employees": 120, "industry_sector": "Manufacturing"},
    )
    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["total_employees"] == 120
    assert metadata["industry_sector"] == "Manufacturing"


def test_update_metadata_requires_admin(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.put(
        "/api/v3/organizations/org-a/metadata", json={"total_employees": 120}
    ).status_code == 403


def test_update_metadata_org_isolation(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.put(
        "/api/v3/organizations/org-b/metadata", json={"total_employees": 120}
    ).status_code == 403


# ---------------------------------------------------------------------------
# Members + roles
# ---------------------------------------------------------------------------


def _seed_member(world, member_id, org_id, role="admin", email=None):
    world.organizations.add_member_record({
        "id": member_id,
        "organization_id": org_id,
        "user_id": f"u-{member_id}",
        "role": role,
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
        "email": email or f"{member_id}@example.test",
    })


def test_list_members(client, world, user_provider) -> None:
    _seed_member(world, "member-1", "org-a", role="admin", email="u1@example.test")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/members")
    assert response.status_code == 200
    members = response.json()["members"]
    assert [m["id"] for m in members] == ["member-1"]
    assert members[0]["email"] == "u1@example.test"


def test_list_members_org_isolation(client, world, user_provider) -> None:
    _seed_member(world, "member-b", "org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/members").status_code == 403


def test_get_member_detail(client, world, user_provider) -> None:
    _seed_member(world, "member-1", "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/members/member-1")
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_get_member_detail_nonexistent(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/members/does-not-exist").status_code == 404


def test_get_member_detail_cross_org(client, world, user_provider) -> None:
    _seed_member(world, "member-b", "org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/members/member-b").status_code == 403


def test_add_member_validates_role(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/members",
        json={"user_id": "u-9", "role": "superadmin"},
    )
    assert response.status_code == 422


def test_add_member_requires_admin(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/members",
        json={"user_id": "u-9", "role": "member"},
    )
    assert response.status_code == 403


def test_update_member_validates_role(client, world, user_provider) -> None:
    world.tenant.seed_member({
        "id": "member-1",
        "organization_id": "org-a",
        "user_id": "u-1",
        "role": "member",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.put(
        "/api/v3/organizations/members/member-1", json={"role": "ceo"}
    ).status_code == 422


def test_update_member_org_admin(client, world, user_provider) -> None:
    world.tenant.seed_member({
        "id": "member-1",
        "organization_id": "org-a",
        "user_id": "u-1",
        "role": "member",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.put(
        "/api/v3/organizations/members/member-1", json={"role": "viewer"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_remove_member_cross_org_denied(client, world, user_provider) -> None:
    _seed_member(world, "member-b", "org-b")
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.delete("/api/v3/organizations/members/member-b").status_code == 403


def test_list_org_roles(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/roles")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["roles"]]
    assert ids == ["owner", "admin", "member", "viewer"]


def test_list_org_roles_cross_org(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/roles").status_code == 403


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


def test_invitations_requires_admin(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-a/invitations").status_code == 403


def test_create_invitation_admin(client, world, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/invitations",
        json={"email": "new@example.test", "role": "member"},
    )
    assert response.status_code == 201
    invitation = response.json()
    assert invitation["email"] == "new@example.test"
    assert invitation["status"] == "pending"
    assert invitation["organization_id"] == "org-a"
    assert invitation["invited_by"] == "admin-a"
    assert invitation["token"]


def test_create_invitation_validates_role(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/invitations",
        json={"email": "new@example.test", "role": "superadmin"},
    )
    assert response.status_code == 422


def test_create_invitation_cross_org_denied(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.post(
        "/api/v3/organizations/org-b/invitations",
        json={"email": "new@example.test", "role": "member"},
    )
    assert response.status_code == 403


def test_list_invitations_org_scoped(client, world, user_provider) -> None:
    import asyncio

    asyncio.run(world.invitations.create(
        "org-a", "a@example.test", token="tok-a", invited_by="admin-a"
    ))
    asyncio.run(world.invitations.create(
        "org-b", "b@example.test", token="tok-b", invited_by="admin-b"
    ))
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.get("/api/v3/organizations/org-a/invitations")
    assert response.status_code == 200
    emails = [i["email"] for i in response.json()["invitations"]]
    assert emails == ["a@example.test"]


def test_list_invitations_cross_org_denied(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.get("/api/v3/organizations/org-b/invitations").status_code == 403


def test_revoke_invitation(client, world, user_provider) -> None:
    import asyncio

    invitation = asyncio.run(world.invitations.create(
        "org-a", "a@example.test", token="tok-a", invited_by="admin-a"
    ))
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    response = client.delete(f"/api/v3/organizations/invitations/{invitation['id']}")
    assert response.status_code == 204
    stored = asyncio.run(world.invitations.get(invitation["id"]))
    assert stored["status"] == "revoked"


def test_revoke_invitation_cross_org_denied(client, world, user_provider) -> None:
    import asyncio

    invitation = asyncio.run(world.invitations.create(
        "org-b", "b@example.test", token="tok-b", invited_by="admin-b"
    ))
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.delete(
        f"/api/v3/organizations/invitations/{invitation['id']}"
    ).status_code == 403


def test_revoke_invitation_nonexistent(client, user_provider) -> None:
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))
    assert client.delete(
        "/api/v3/organizations/invitations/does-not-exist"
    ).status_code == 404


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------


def _seed_supplier(world, supplier_id, org_id, name, category_id=None, is_active=True):
    world.suppliers.seed({
        "id": supplier_id,
        "organization_id": org_id,
        "name": name,
        "type": None,
        "supplier_category_id": category_id,
        "contact_name": None,
        "contact_email": f"{supplier_id}@example.test",
        "contact_phone": None,
        "country": "GB",
        "vat_number": None,
        "website": None,
        "supplier_type": None,
        "annual_emissions": None,
        "supplier_rating": None,
        "is_certified": False,
        "is_active": is_active,
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
        "metadata": {},
    })


def test_list_suppliers_org_isolated(client, world, user_provider) -> None:
    _seed_supplier(world, "sup-a", "org-a", "Acme")
    _seed_supplier(world, "sup-b", "org-b", "Other")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/suppliers", params={"organization_id": "org-a"})
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()["suppliers"]]
    assert ids == ["sup-a"]


def test_list_suppliers_cross_org_denied(client, world, user_provider) -> None:
    _seed_supplier(world, "sup-b", "org-b", "Other")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get(
        "/api/v3/suppliers", params={"organization_id": "org-b"}
    ).status_code == 403


def test_suppliers_search_filter(client, world, user_provider) -> None:
    _seed_supplier(world, "sup-1", "org-a", "Acme Energy", category_id="cat-1")
    _seed_supplier(world, "sup-2", "org-a", "Beta Logistics")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))

    search = client.get(
        "/api/v3/suppliers",
        params={"organization_id": "org-a", "search": "energy"},
    ).json()
    assert [s["id"] for s in search["suppliers"]] == ["sup-1"]

    by_category = client.get(
        "/api/v3/suppliers",
        params={"organization_id": "org-a", "category_id": "cat-1"},
    ).json()
    assert [s["id"] for s in by_category["suppliers"]] == ["sup-1"]


def test_suppliers_status_filter(client, world, user_provider) -> None:
    _seed_supplier(world, "sup-1", "org-a", "Active Co", is_active=True)
    _seed_supplier(world, "sup-2", "org-a", "Inactive Co", is_active=False)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    active = client.get(
        "/api/v3/suppliers",
        params={"organization_id": "org-a", "status": "active"},
    ).json()
    assert [s["id"] for s in active["suppliers"]] == ["sup-1"]


def test_get_supplier_detail_cross_org(client, world, user_provider) -> None:
    _seed_supplier(world, "sup-b", "org-b", "Other")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/suppliers/sup-b").status_code == 403


def test_get_supplier_detail_nonexistent(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/suppliers/does-not-exist").status_code == 404


# ---------------------------------------------------------------------------
# Facilities + assets
# ---------------------------------------------------------------------------


def test_list_facilities_org_isolated(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/facilities")
    assert response.status_code == 200
    # Seed Org A has one facility ("HQ"). The API returns JSON dict rows.
    assert [f["id"] for f in response.json()["facilities"]] == ["fac-a1"]


def test_list_facilities_cross_org(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/facilities").status_code == 403


def test_facility_detail_with_assets(client, world, user_provider) -> None:
    world.tenant.seed_facility({
        "id": "fac-1",
        "organization_id": "org-a",
        "name": "London HQ",
        "postcode": "EC1A 1AA",
        "country": "GB",
        "type": "office",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/facilities/fac-1")
    assert response.status_code == 200
    body = response.json()
    assert body["facility"]["name"] == "London HQ"
    # Assets of the facility come from the org's real asset rows.
    assert "assets" in body


def test_facility_detail_cross_org(client, world, user_provider) -> None:
    world.tenant.seed_facility({
        "id": "fac-b",
        "organization_id": "org-b",
        "name": "B HQ",
        "postcode": "D01",
        "country": "IE",
        "type": "office",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/facilities/fac-b").status_code == 403


def test_facility_detail_nonexistent(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/facilities/does-not-exist").status_code == 404


def test_list_assets_org_isolated(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/org-a/assets")
    assert response.status_code == 200
    # Seed Org A has one asset ("Boiler"). The API returns JSON dict rows.
    assert [a["id"] for a in response.json()["assets"]] == ["asset-a1"]


def test_list_assets_cross_org(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/org-b/assets").status_code == 403


def test_asset_detail(client, world, user_provider) -> None:
    world.tenant.seed_asset({
        "id": "asset-1",
        "organization_id": "org-a",
        "facility_id": "fac-a1",
        "name": "Boiler B",
        "type": "boiler",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/organizations/assets/asset-1")
    assert response.status_code == 200
    assert response.json()["name"] == "Boiler B"


def test_asset_detail_cross_org(client, world, user_provider) -> None:
    world.tenant.seed_asset({
        "id": "asset-b",
        "organization_id": "org-b",
        "facility_id": "fac-b1",
        "name": "B Asset",
        "type": "boiler",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/assets/asset-b").status_code == 403


def test_asset_detail_nonexistent(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/organizations/assets/does-not-exist").status_code == 404






# ---------------------------------------------------------------------------
# Organisation OWNER org-admin capabilities (P1-F4)
# The schema's RLS treats `owner` as an org administrator (om_insert_admin /
# om_update_admin use role IN ('owner','admin')); require_org_admin must
# recognise the owner of an organisation as its administrator.
# ---------------------------------------------------------------------------


def test_owner_can_create_facility(client, world, user_provider) -> None:
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/facilities",
        json={"name": "Owner Depot", "postcode": "LE1 1AA", "country": "GB", "type": "warehouse"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Owner Depot"


def test_owner_can_create_asset(client, world, user_provider) -> None:
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/assets",
        json={"facility_id": "facility-a", "name": "Owner boiler", "type": "boiler"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Owner boiler"


def test_owner_can_create_invitation(client, world, user_provider) -> None:
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/invitations",
        json={"email": "owner-invite@example.test", "role": "member"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "owner-invite@example.test"
    assert response.json()["invited_by"] == "owner-a"


def test_member_cannot_create_facility(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/organizations/org-a/facilities",
        json={"name": "No", "postcode": "LE1 1AA", "country": "GB"},
    )
    assert response.status_code == 403

