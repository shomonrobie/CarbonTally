"""D37-0 — commercial configuration + billing-security unit contract tests.

Covers the trusted ``/api/v3/commercial/*`` surface and the configurable
subscription foundation:

* authorization matrix — platform billing admins only (customers, consultants,
  Processing Entity staff and staff without ``can_manage_billing`` are denied);
* versioned commercial config (new version per change, history preserved);
* versioned plan catalogue (plan changes publish a new version);
* the append-only credit ledger (record/balance/idempotency);
* per-customer ``billing_mode`` assigned from the versioned default at org
  creation (D37-0 §11 — changing the default never rewrites existing orgs).

All tests run in-memory (no database access).
"""
from __future__ import annotations

import asyncio

from domain.billing import CreditLedgerEntry
from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import (
    entity_operator_user,
    member_user,
    staff_user,
)
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/commercial/overview",
    "/api/v3/commercial/config",
    "/api/v3/commercial/config/{config_key}",
    "/api/v3/commercial/plans",
    "/api/v3/commercial/plans/{plan_code}",
    "/api/v3/commercial/ledger",
    "/api/v3/commercial/organizations",
)


def _seed_staff(world, *, user_id: str = "u-billing", entity_id=None) -> None:
    """Seed an active staff profile bound to a role with can_manage_billing."""
    world.staff.seed_role(
        StaffRole(
            id="role-billing",
            name="billing_admin",
            permissions={
                "can_manage_billing": True,
                "can_view_all": True,
            },
        )
    )
    world.staff.seed_role(
        StaffRole(
            id="role-plain",
            name="staff",
            permissions={"can_view_all": True},
        )
    )
    world.staff.seed_profile(
        StaffProfile(
            id="sp-billing",
            user_id=user_id,
            first_name="Bill",
            last_name="Admin",
            email="billing@carbontally.test",
            role_id="role-billing",
            entity_id=entity_id,
            is_active=True,
        )
    )
    world.staff.seed_profile(
        StaffProfile(
            id="sp-plain",
            user_id="u-plain",
            first_name="Plain",
            last_name="Staff",
            email="plain@carbontally.test",
            role_id="role-plain",
            entity_id=None,
            is_active=True,
        )
    )


def _billing_admin() -> "object":
    return staff_user("u-billing", email="billing@carbontally.test")


def test_commercial_routes_registered(client) -> None:
    paths = flatten_router_paths(client.app)
    for fragment in EXPECTED_PATH_FRAGMENTS:
        assert fragment in paths, f"missing route {fragment}"


# ---------------------------------------------------------------------------
# Authorization matrix (D37-0 §24/§30)
# ---------------------------------------------------------------------------


def test_commercial_overview_unauthenticated(client, world, user_provider) -> None:
    user_provider.set_unauthenticated()
    assert client.get("/api/v3/commercial/overview").status_code == 401


def test_commercial_overview_customer_denied(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/commercial/overview").status_code == 403


def test_commercial_overview_consultant_denied(client, world, user_provider) -> None:
    from tests.unit.api.fakes import consultant_user

    _seed_staff(world)
    user_provider.set_user(consultant_user("u-consult", "consult@test"))
    assert client.get("/api/v3/commercial/overview").status_code == 403


def test_commercial_overview_entity_staff_denied(client, world, user_provider) -> None:
    _seed_staff(world, user_id="u-ent", entity_id="entity-1")
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    # Entity staff have an active profile but are NOT CarbonTally internal.
    assert client.get("/api/v3/commercial/overview").status_code == 403


def test_commercial_overview_plain_staff_denied(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(staff_user("u-plain", email="plain@carbontally.test"))
    assert client.get("/api/v3/commercial/overview").status_code == 403


def test_commercial_overview_billing_admin_allowed(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    response = client.get("/api/v3/commercial/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["default_billing_mode"] == "CREDIT"
    assert set(body["billing_modes"]) == {"CREDIT", "STANDARD"}
    assert "default_billing_mode" in body["config"]

# ---------------------------------------------------------------------------
# Versioned commercial configuration (D37-0 §23)
# ---------------------------------------------------------------------------


def test_config_update_publishes_new_version_preserving_history(
    client, world, user_provider
) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    assert asyncio.run(world.billing_config.get_current("credit_rules")).version == 1

    response = client.put(
        "/api/v3/commercial/config/credit_rules",
        json={
            "config_value": {"classes": [{"class": "simple", "credits": 2}]},
            "reason": "rebalance simple class",
        },
    )
    assert response.status_code == 200
    current = asyncio.run(world.billing_config.get_current("credit_rules"))
    assert current.version == 2
    assert current.config_value["classes"][0]["credits"] == 2

    # History is never rewritten — version 1 is intact.
    history = asyncio.run(world.billing_config.history("credit_rules"))
    assert [h.version for h in history] == [1, 2]
    assert history[0].config_value["classes"][0]["credits"] == 1

    # The API exposes current + full history.
    detail = client.get("/api/v3/commercial/config/credit_rules").json()
    assert detail["current"]["version"] == 2
    assert [h["version"] for h in detail["history"]] == [1, 2]


def test_default_billing_mode_change_is_versioned_and_validated(
    client, world, user_provider
) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    assert asyncio.run(world.billing_config.get_default_billing_mode()) == "CREDIT"

    response = client.put(
        "/api/v3/commercial/config/default_billing_mode",
        json={"config_value": {"mode": "STANDARD"}, "reason": "switch default"},
    )
    assert response.status_code == 200
    assert asyncio.run(world.billing_config.get_default_billing_mode()) == "STANDARD"
    assert asyncio.run(world.billing_config.get_current("default_billing_mode")).version == 2

    # Invalid mode rejected at the API layer.
    response = client.put(
        "/api/v3/commercial/config/default_billing_mode",
        json={"config_value": {"mode": "GOLD_PLATED"}},
    )
    assert response.status_code == 422

    # Unknown config keys rejected.
    response = client.put(
        "/api/v3/commercial/config/not_a_real_key",
        json={"config_value": {}},
    )
    assert response.status_code == 404


def test_config_change_is_audited(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    client.put(
        "/api/v3/commercial/config/storage",
        json={"config_value": {"included_bytes": 1}, "reason": "storage test"},
    )
    entries = [e for e in world.audit._entries if e.entity_type == "billing_commercial_config"]
    assert any(e.action == "commercial_config.updated" and e.entity_id == "storage" for e in entries)



def test_commercial_write_requires_billing_admin(client, world, user_provider) -> None:
    # Plain internal staff may read nothing and write nothing.
    _seed_staff(world)
    user_provider.set_user(staff_user("u-plain", email="plain@carbontally.test"))
    response = client.put(
        "/api/v3/commercial/config/credit_rules",
        json={"config_value": {"classes": []}, "reason": "x"},
    )
    assert response.status_code == 403
    response = client.post(
        "/api/v3/commercial/plans",
        json={"plan_code": "hacked", "name": "Hacked"},
    )
    assert response.status_code == 403

# ---------------------------------------------------------------------------
# Versioned plan catalogue (D37-0 §13)
# ---------------------------------------------------------------------------


def test_plan_created_then_versioned(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    assert asyncio.run(world.billing_plans.list_current()) == []

    response = client.post(
        "/api/v3/commercial/plans",
        json={
            "plan_code": "starter",
            "name": "Starter",
            "price": 49,
            "included_credits": 50,
        },
    )
    assert response.status_code == 201
    assert asyncio.run(world.billing_plans.get_current_by_code("starter")).version == 1

    # Same code again -> 409 (use PUT to version).
    response = client.post(
        "/api/v3/commercial/plans",
        json={"plan_code": "starter", "name": "Starter 2"},
    )
    assert response.status_code == 409

    # Publish v2 with a price change.
    response = client.put(
        "/api/v3/commercial/plans/starter",
        json={"price": 59, "reason": "price review"},
    )
    assert response.status_code == 200
    assert response.json()["previous_version"] == 1
    current = asyncio.run(world.billing_plans.get_current_by_code("starter"))
    assert current.version == 2
    assert current.price == 59

    # Historical terms intact.
    history = asyncio.run(world.billing_plans.history("starter"))
    assert [h.version for h in history] == [1, 2]
    assert history[0].price == 49
    assert history[0].effective_to is not None
    assert history[1].effective_to is None


def test_plan_update_invalid_mode_rejected(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    client.post(
        "/api/v3/commercial/plans",
        json={"plan_code": "basic", "name": "Basic"},
    )
    response = client.put(
        "/api/v3/commercial/plans/basic",
        json={"billing_mode": "BOGUS"},
    )
    assert response.status_code == 422


def test_plan_change_is_audited(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    client.post(
        "/api/v3/commercial/plans",
        json={"plan_code": "pro", "name": "Pro"},
    )
    client.put("/api/v3/commercial/plans/pro", json={"price": 149})
    entries = [e for e in world.audit._entries if e.entity_type == "billing_plan"]
    assert any(e.action == "plan.created" for e in entries)
    assert any(e.action == "plan.version_published" for e in entries)


# ---------------------------------------------------------------------------
# Append-only credit ledger (D37-0 §22)
# ---------------------------------------------------------------------------


def test_ledger_records_and_derives_balance(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(_billing_admin())
    asyncio.run(
        world.billing_ledger.record(
            CreditLedgerEntry(
                id="l1", organization_id="org-a", entry_type="grant",
                credit_delta=500, source="plan_included", plan_code="professional",
                plan_version=1, external_reference="ref-1",
            )
        )
    )
    asyncio.run(
        world.billing_ledger.record(
            CreditLedgerEntry(
                id="l2", organization_id="org-a", entry_type="consume",
                credit_delta=-120, source="adjustment", reason="doc processing",
                external_reference="ref-2",
            )
        )
    )
    response = client.get("/api/v3/commercial/ledger?organization_id=org-a")
    assert response.status_code == 200
    body = response.json()
    assert body["balance"] == 380
    assert len(body["entries"]) == 2


def test_ledger_idempotency_via_external_reference(world) -> None:
    asyncio.run(
        world.billing_ledger.record(
            CreditLedgerEntry(
                id="l1", organization_id="org-a", entry_type="grant",
                credit_delta=100, source="plan_included", external_reference="evt-1",
            )
        )
    )
    try:
        asyncio.run(
            world.billing_ledger.record(
                CreditLedgerEntry(
                    id="l2", organization_id="org-a", entry_type="grant",
                    credit_delta=100, source="plan_included", external_reference="evt-1",
                )
            )
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("duplicate external_reference must be rejected")
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 100


def test_ledger_read_requires_billing_admin(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/commercial/ledger?organization_id=org-a").status_code == 403


# ---------------------------------------------------------------------------
# Per-customer billing mode (D37-0 §11)
# ---------------------------------------------------------------------------


def test_org_creation_assigns_versioned_default_mode(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(
        member_user("org-a", "user-new", "new.user@test")
    )
    response = client.post(
        "/api/v3/organizations",
        json={"name": "Mode Org", "country": "GB"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    org = body.get("organization") or body
    org_id = org.get("id") if isinstance(org, dict) else org
    assert asyncio.run(world.organizations.get_billing_mode(org_id)) == "CREDIT"


def test_org_creation_uses_latest_default_after_admin_change(
    client, world, user_provider
) -> None:
    _seed_staff(world)
    # Admin flips the default to STANDARD.
    user_provider.set_user(_billing_admin())
    response = client.put(
        "/api/v3/commercial/config/default_billing_mode",
        json={"config_value": {"mode": "STANDARD"}, "reason": "switch"},
    )
    assert response.status_code == 200
    assert asyncio.run(world.billing_config.get_default_billing_mode()) == "STANDARD"

    # A NEW customer gets STANDARD.
    user_provider.set_user(member_user("org-a", "user-new", "new.user@test"))
    response = client.post(
        "/api/v3/organizations",
        json={"name": "Standard Mode Org", "country": "GB"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    org = body.get("organization") or body
    org_id = org.get("id") if isinstance(org, dict) else org
    assert asyncio.run(world.organizations.get_billing_mode(org_id)) == "STANDARD"

    # EXISTING orgs keep their original mode (no silent migration).
    assert asyncio.run(world.organizations.get_billing_mode("org-a")) is None

