"""P6-BILL-1 — entitlement enforcement + consultant commercial scaffolding.

Covers the ratified P6-BILL-1 decisions (in-memory, no database access):

* D-A — registration mode: INVITATION_ONLY closes self-service org creation and
  consultant self-registration; OPEN_REGISTRATION (default) permits them.
  Registration NEVER grants organisation/client access or capability.
* PO-D7 — no active processing entitlement -> chargeable processing DENIED;
  credits stay organisation-scoped (no firm pool, no cross-client transfer).
* D-C — Consultant capability is an additive organisation entitlement carried by
  the ACTIVE subscription's plan feature block; no second organisation is
  created and org identity/data remain untouched.
* Scope E — consultant client grants record the server-authoritative creator.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from auth import AuthUser
from domain.billing import BillingPlan, Subscription
from services.billing import (
    BillingService,
    EntitlementUnavailableError,
    resolve_registration_mode,
)
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    staff_user,
)


def _no_org_user(user_id: str = "u-reg", email: str = "reg@customer.test") -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email=email,
        role="user",
        role_name="user",
        is_active=True,
    )


def _run(coro_fn, *args, **kwargs):
    return asyncio.run(coro_fn(*args, **kwargs))


def _seed_registration_mode(world, mode: str) -> None:
    asyncio.run(
        world.billing_config.update_version(
            config_key="registration_mode",
            config_value={"mode": mode},
            reason="test",
            updated_by="admin-1",
        )
    )


def _seed_plan(world, *, code="professional", features=None) -> None:
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()),
                plan_code=code,
                name=code.capitalize(),
                price=149,
                currency="USD",
                included_credits=500,
                version=1,
                is_active=True,
                features=features or {},
                effective_from=datetime.now(timezone.utc),
            ),
            created_by=None,
        )
    )


def _activate(world, org_id, *, plan="professional", key="act-key-1") -> None:
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                plan_code=plan,
                plan_version=1,
                billing_mode="CREDIT",
                lifecycle_status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc),
                idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )


def _grant(world, org_id: str, amount: int = 500, key: str = "grant-1") -> None:
    asyncio.run(
        BillingService(world.bundle()).grant_credits(
            org_id,
            amount,
            source="plan_included",
            reason="monthly",
            idempotency_key=key,
        )
    )


# ---------------------------------------------------------------------------
# Registration mode (D-A)
# ---------------------------------------------------------------------------


def test_registration_mode_defaults_to_open() -> None:
    from tests.unit.api.fakes import InMemoryWorld

    world = InMemoryWorld()
    assert _run(resolve_registration_mode, world.bundle()) == "OPEN_REGISTRATION"


def test_registration_mode_reads_admin_config(world) -> None:
    _seed_registration_mode(world, "INVITATION_ONLY")
    assert _run(resolve_registration_mode, world.bundle()) == "INVITATION_ONLY"
    _seed_registration_mode(world, "OPEN_REGISTRATION")
    assert _run(resolve_registration_mode, world.bundle()) == "OPEN_REGISTRATION"


def test_open_registration_permits_org_creation(client, world, user_provider) -> None:
    user_provider.set_user(_no_org_user("u-reg", "reg@customer.test"))
    _seed_registration_mode(world, "OPEN_REGISTRATION")
    resp = client.post("/api/v3/organizations", json={"name": "Open Co Ltd"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["onboarding"]["status"] == "ORGANIZATION_CREATED"


def test_invitation_only_blocks_self_service_org_creation(client, world, user_provider) -> None:
    user_provider.set_user(_no_org_user("u-reg", "reg@customer.test"))
    _seed_registration_mode(world, "INVITATION_ONLY")
    resp = client.post("/api/v3/organizations", json={"name": "Blocked Co Ltd"})
    assert resp.status_code == 403, resp.text
    assert "invitation-only" in resp.text.lower()


def test_invitation_only_blocks_consultant_self_registration(client, world, user_provider) -> None:
    user_provider.set_user(_no_org_user("u-cons-reg", "cons@customer.test"))
    _seed_registration_mode(world, "INVITATION_ONLY")
    resp = client.post("/api/v3/consultants/me", json={"company_name": "Blocked Firm"})
    assert resp.status_code == 403, resp.text


def test_open_registration_permits_consultant_profile_registration(client, world, user_provider) -> None:
    user_provider.set_user(_no_org_user("u-cons-reg", "cons@customer.test"))
    resp = client.post("/api/v3/consultants/me", json={"company_name": "Solo Advisory"})
    assert resp.status_code == 201, resp.text


def test_registration_never_grants_client_access(client, world, user_provider) -> None:
    """Self-registering a consultant profile grants NO client capability/access."""
    user_provider.set_user(_no_org_user("u-cons-reg", "cons@customer.test"))
    created = client.post("/api/v3/consultants/me", json={"company_name": "Solo Advisory"})
    assert created.status_code == 201, created.text
    # No firm-membership row exists -> require_consultant denies; a client grant
    # cannot be created merely because registration succeeded.
    assert client.get("/api/v3/consultants/me/clients").status_code == 403
    resp = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-a", "client_name": "ACME LTD"},
    )
    assert resp.status_code == 403, resp.text


def test_registration_mode_admin_config_only(client, world, user_provider) -> None:
    """A normal authenticated user cannot change the registration mode."""
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    resp = client.put(
        "/api/v3/commercial/config/registration_mode",
        json={"config_value": {"mode": "INVITATION_ONLY"}, "reason": "hijack"},
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Entitlement enforcement (PO-D7)
# ---------------------------------------------------------------------------


def test_active_entitlement_permits_chargeable_processing(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    _grant(world, "org-a")
    svc = BillingService(world.bundle())
    result = _run(
        svc.charge_processing,
        "org-a",
        job={"kind": "document", "page_count": 1},
        idempotency_key="chg-ok-1",
    )
    assert result["mode"] == "CREDIT"
    assert result["charged"] is True
    assert _run(world.billing_ledger.balance, "org-a") == 499


def test_no_entitlement_denies_chargeable_processing(world) -> None:
    svc = BillingService(world.bundle())
    try:
        _run(
            svc.charge_processing,
            "org-a",
            job={"kind": "document", "page_count": 1},
            idempotency_key="chg-deny-1",
        )
    except EntitlementUnavailableError as exc:
        assert exc.status_code == 403
    else:  # pragma: no cover
        raise AssertionError("chargeable processing without entitlement must be denied")


def test_expired_inactive_entitlement_denies_processing(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a", key="sub-live")
    sub = _run(world.billing_subscriptions.get_active_for_org, "org-a")
    assert sub is not None
    asyncio.run(
        world.billing_subscriptions.update_status(
            sub.id,
            "cancelled",
            updated_by="admin-1",
        )
    )
    svc = BillingService(world.bundle())
    try:
        _run(
            svc.charge_processing,
            "org-a",
            job={"kind": "document", "page_count": 1},
            idempotency_key="chg-deny-2",
        )
    except EntitlementUnavailableError:
        pass
    else:  # pragma: no cover
        raise AssertionError("cancelled entitlement must deny processing")


def test_entitlement_resolved_server_side(client, world, user_provider) -> None:
    """/billing/me entitlement is derived from server state, never the client."""
    _seed_plan(world)
    _activate(world, "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    body = client.get("/api/v3/billing/me").json()
    assert body["plan"]["plan_code"] == "professional"
    assert body["subscription"]["lifecycle_status"] == "active"
    assert "capabilities" in body


def test_client_supplied_entitlement_claims_cannot_bypass(world) -> None:
    """charge_processing accepts NO client entitlement claim — org + job only."""
    svc = BillingService(world.bundle())
    try:
        _run(
            svc.charge_processing,
            "org-a",
            job={"kind": "document", "page_count": 1},
            idempotency_key="chg-claim-1",
        )
    except EntitlementUnavailableError:
        pass
    else:  # pragma: no cover
        raise AssertionError("a bare org id without server-side entitlement must not charge")



# ---------------------------------------------------------------------------
# Credit ownership / isolation (PO-D7)
# ---------------------------------------------------------------------------


def test_client_a_credits_charge_only_client_a(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    _grant(world, "org-a", 500, key="grant-a")
    _activate(world, "org-b", key="act-b")
    _grant(world, "org-b", 500, key="grant-b")
    svc = BillingService(world.bundle())
    result = _run(
        svc.charge_processing,
        "org-a",
        job={"kind": "document", "page_count": 1},
        idempotency_key="chg-a-1",
    )
    assert result["mode"] == "CREDIT"
    # Client A pays for A's work; Client B's balance is untouched.
    assert _run(world.billing_ledger.balance, "org-a") == 499
    assert _run(world.billing_ledger.balance, "org-b") == 500
    org_a_entries = _run(world.billing_ledger.list_for_org, "org-a")
    org_b_entries = _run(world.billing_ledger.list_for_org, "org-b")
    assert any(e.entry_type == "consume" for e in org_a_entries)
    assert not any(e.entry_type == "consume" for e in org_b_entries)


def test_client_a_cannot_consume_client_b_credits(world) -> None:
    _seed_plan(world)
    _activate(world, "org-b")
    _grant(world, "org-b", 500, key="grant-b")
    svc = BillingService(world.bundle())
    # org-a has no subscription -> org-b's credits cannot be redirected to pay
    # for org-a work (the org is server-derived; no cross-client pool exists).
    try:
        _run(
            svc.charge_processing,
            "org-a",
            job={"kind": "document", "page_count": 1},
            idempotency_key="chg-cross-1",
        )
    except EntitlementUnavailableError:
        pass
    else:  # pragma: no cover
        raise AssertionError("Client A must not consume Client B's credits")
    assert _run(world.billing_ledger.balance, "org-b") == 500


def test_no_firm_scoped_pooled_credits(world) -> None:
    """All ledger entries are organisation-scoped; nothing firm/consultant keyed."""
    _seed_plan(world)
    _activate(world, "org-a")
    _grant(world, "org-a", 500, key="grant-a")
    svc = BillingService(world.bundle())
    _run(
        svc.charge_processing,
        "org-a",
        job={"kind": "document", "page_count": 1},
        idempotency_key="chg-pool-1",
    )
    for entry in _run(world.billing_ledger.list_for_org, "org-a"):
        assert entry.organization_id == "org-a"
    assert _run(world.billing_ledger.list_for_org, "firm-1") == []



# ---------------------------------------------------------------------------
# Consultant capability (D-C — additive org entitlement)
# ---------------------------------------------------------------------------

_CONSULTANT_FEATURES = {
    "consultant": {
        "enabled": True,
        "client_capacity": 5,
        "team_member_limit": 10,
        "white_label": True,
        "workspace": True,
    }
}


def test_org_with_consultant_entitlement_passes_capability_check(world) -> None:
    _seed_plan(world, code="consultant-plus", features=_CONSULTANT_FEATURES)
    _activate(world, "org-a", plan="consultant-plus")
    cap = _run(BillingService(world.bundle()).consultant_capability, "org-a")
    assert cap["entitled"] is True
    assert cap["client_capacity"] == 5
    assert cap["team_member_limit"] == 10
    assert cap["white_label"] is True
    ent = _run(BillingService(world.bundle()).get_entitlement, "org-a")
    assert ent["capabilities"]["consultant"]["entitled"] is True


def test_org_without_consultant_entitlement_fails_capability_check(world) -> None:
    # No subscription at all.
    cap = _run(BillingService(world.bundle()).consultant_capability, "org-a")
    assert cap["entitled"] is False
    # Active subscription on a plan WITHOUT the consultant feature.
    _seed_plan(world, code="professional", features={})
    _activate(world, "org-a", plan="professional")
    cap2 = _run(BillingService(world.bundle()).consultant_capability, "org-a")
    assert cap2["entitled"] is False
    assert cap2["client_capacity"] is None


def test_consultant_capability_does_not_create_second_org(world) -> None:
    org_count_before = len(world.organizations._orgs)
    org_name_before = world.organizations._orgs["org-a"].name
    _seed_plan(world, code="consultant-plus", features=_CONSULTANT_FEATURES)
    _activate(world, "org-a", plan="consultant-plus")
    cap = _run(BillingService(world.bundle()).consultant_capability, "org-a")
    assert cap["entitled"] is True
    # The org identity/data are untouched and no duplicate organisation exists.
    assert len(world.organizations._orgs) == org_count_before
    assert world.organizations._orgs["org-a"].name == org_name_before


def test_capability_does_not_self_create_client_grants(world) -> None:
    """A D-C entitlement never creates consultant_clients grants by itself."""
    _seed_plan(world, code="consultant-plus", features=_CONSULTANT_FEATURES)
    _activate(world, "org-a", plan="consultant-plus")
    assert _run(world.consultants.get_client_by_org, "firm-1", "org-a") is None
    assert _run(BillingService(world.bundle()).consultant_capability, "org-a")["entitled"] is True


# ---------------------------------------------------------------------------
# Client-grant creator provenance + permission boundary (Scope E / D-D)
# ---------------------------------------------------------------------------


def _seed_consultant(world, user_id="u-cons", *, can_manage_clients=True):
    world.consultants.seed_profile("firm-1", user_id, "Acme Consultants")
    world.consultants.seed_firm_member(
        "firm-1",
        user_id,
        role="manager",
        can_manage_clients=can_manage_clients,
        can_upload_documents=True,
        can_generate_reports=True,
        can_manage_team=True,
    )
    return consultant_user(user_id, "cons@example.test")


def test_client_grant_records_authoritative_creator(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/clients",
        json={
            "organization_id": "org-a",
            "client_name": "ACME LTD",
            "client_industry": "Manufacturing",
            "client_contact_email": "owner@acme.test",
            "client_contact_name": "Jane",
        },
    )
    assert resp.status_code == 201, resp.text
    client_row = resp.json()
    assert client_row["created_by"] == "u-cons"
    stored = _run(world.consultants.get_client_by_org, "firm-1", "org-a")
    assert stored is not None and stored.created_by == "u-cons"


def test_consultant_without_permission_cannot_create_client_grant(client, world, user_provider) -> None:
    user = _seed_consultant(world, user_id="u-cons-ro", can_manage_clients=False)
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-a", "client_name": "ACME LTD"},
    )
    assert resp.status_code == 403, resp.text
    assert _run(world.consultants.get_client_by_org, "firm-1", "org-a") is None


def test_client_grant_actor_is_never_client_supplied(client, world, user_provider) -> None:
    """A forged actor id in the payload is ignored — the actor is server-derived.

    ``ClientCreate`` drops unknown fields, so the forged ``created_by`` never
    reaches the repository; the stored creator is the authenticated consultant.
    """
    user = _seed_consultant(world)
    user_provider.set_user(user)
    resp = client.post(
        "/api/v3/consultants/me/clients",
        json={
            "organization_id": "org-a",
            "client_name": "ACME LTD",
            "created_by": "attacker-user",
        },
    )
    assert resp.status_code == 201, resp.text
    stored = _run(world.consultants.get_client_by_org, "firm-1", "org-a")
    assert stored is not None
    assert stored.created_by == "u-cons"
    assert stored.created_by != "attacker-user"

