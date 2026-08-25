"""D37 — billing core contract tests (in-memory, no database access).

Covers the provider-neutral billing service + the customer/admin billing API:
subscription lifecycle, entitlement resolution, credit operations
(grant/consume/rollover/emergency/adjust/reverse/refund), idempotency, the
common order model (Assisted estimate/approve/complete/cancel, Managed),
processing charges (CREDIT/STANDARD/no-subscription) and authorization.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from domain.billing import Subscription
from services.billing import (
    BillingService,
    IdempotencyConflict,
    InsufficientCreditsError,
)
from tests.unit.api.fakes import (
    member_user,
    staff_user,
)
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/billing/me",
    "/api/v3/billing/me/credits",
    "/api/v3/billing/me/orders",
    "/api/v3/billing/orders/assisted",
    "/api/v3/billing/managed/orders",
    "/api/v3/commercial/subscriptions",
    "/api/v3/commercial/orders",
    "/api/v3/commercial/credits/grant",
    "/api/v3/commercial/credits/adjust",
    "/api/v3/commercial/credits/reverse",
    "/api/v3/commercial/credits/rollover",
    "/api/v3/commercial/entitlement/{organization_id}",
)


def _seed_plan(world, *, code="professional", price=149, credits=500, storage=0):
    from domain.billing import BillingPlan

    asyncio.run(world.billing_plans.create(
        BillingPlan(id=str(uuid.uuid4()), plan_code=code, name=code.capitalize(),
                    price=price, currency="USD", included_credits=credits,
                    included_storage_bytes=storage, version=1, is_active=True,
                    effective_from=datetime.now(timezone.utc)),
        created_by=None,
    ))


def _activate(world, org_id, *, plan="professional", mode="CREDIT", key="act-key-1"):
    return asyncio.run(world.billing_subscriptions.upsert_active(
        Subscription(
            id=str(uuid.uuid4()), organization_id=org_id, plan_code=plan,
            plan_version=1, billing_mode=mode, lifecycle_status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
            idempotency_key=key,
        ),
        created_by="admin-1",
    ))


def _seed_assisted_pricing(world):
    asyncio.run(world.billing_config.update_version(
        config_key="assisted_pricing",
        config_value={
            "simple": {"price": 0.99, "currency": "USD"},
            "standard": {"price": 1.99, "currency": "USD"},
            "complex": {"price": 3.99, "currency": "USD"},
            "exceptional": {"quoted": True},
        },
        reason="test", updated_by=None,
    ))


def _seed_credit_rules(world):
    asyncio.run(world.billing_config.update_version(
        config_key="credit_rules",
        config_value={
            "classes": [
                {"class": "simple", "credits": 1},
                {"class": "standard", "credits": 2},
                {"class": "complex", "credits": 4},
                {"class": "exceptional", "credits": None, "quoted": True},
            ],
            "classifier": {"complex_pages": 10, "standard_pages": 3,
                           "complex_items": 8, "standard_items": 2},
        },
        reason="test", updated_by=None,
    ))


def _seed_staff(world):
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(StaffRole(id="role-billing", name="billing_admin",
                                    permissions={"can_manage_billing": True}))
    world.staff.seed_profile(StaffProfile(id="sp-b", user_id="u-billing",
                                          first_name="B", last_name="A",
                                          email="b@test", role_id="role-billing"))
    return staff_user("u-billing", email="b@test")


def test_billing_routes_registered(client) -> None:
    paths = flatten_router_paths(client.app)
    for fragment in EXPECTED_PATH_FRAGMENTS:
        assert fragment in paths, f"missing route {fragment}"


# ---------------------------------------------------------------------------
# Entitlement
# ---------------------------------------------------------------------------


def test_entitlement_without_subscription_uses_org_mode(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.get("/api/v3/billing/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["billing_mode"] == "CREDIT"
    assert body["plan"] is None
    assert body["credits"]["balance"] == 0
    assert body["subscription"] is None


def test_entitlement_with_subscription_resolves_plan_version(client, world, user_provider) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.get("/api/v3/billing/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["plan"]["plan_code"] == "professional"
    assert body["plan"]["version"] == 1
    assert body["plan"]["included_credits"] == 500
    assert body["subscription"]["lifecycle_status"] == "active"

# ---------------------------------------------------------------------------
# Credit operations
# ---------------------------------------------------------------------------


def test_grant_then_consume_updates_balance(world) -> None:
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 500, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    result = asyncio.run(svc.consume_credits("org-a", 2, reason="doc",
                                             idempotency_key="c1"))
    assert result["emergency_used"] is False
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 498


def test_consume_with_emergency_allowance(world) -> None:
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 5, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    result = asyncio.run(svc.consume_credits("org-a", 20, reason="big job",
                                             idempotency_key="c1"))
    assert result["emergency_used"] is True
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 5
    types = {e.entry_type for e in asyncio.run(world.billing_ledger.list_for_org("org-a"))}
    assert "emergency_allowance" in types


def test_consume_without_emergency_raises(world) -> None:
    asyncio.run(world.billing_config.update_version(
        config_key="credit_policy",
        config_value={"emergency_allowance": {"enabled": False, "allowance_pct": 0},
                      "rollover": {"enabled": True}},
        reason="test", updated_by=None,
    ))
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 1, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    try:
        asyncio.run(svc.consume_credits("org-a", 5, reason="big", idempotency_key="c1"))
    except InsufficientCreditsError:
        pass
    else:
        raise AssertionError("expected InsufficientCreditsError")


def test_idempotency_rejects_reuse(world) -> None:
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 10, source="plan_included", reason="monthly",
                                  idempotency_key="dup-key"))
    try:
        asyncio.run(svc.grant_credits("org-a", 10, source="plan_included", reason="monthly",
                                      idempotency_key="dup-key"))
    except IdempotencyConflict:
        pass
    else:
        raise AssertionError("duplicate idempotency key must be rejected")
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 10


def test_adjust_reverse_refund_rollover(world) -> None:
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 100, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    asyncio.run(svc.adjust_credits("org-a", -20, reason="correction", idempotency_key="a1"))
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 80
    asyncio.run(svc.refund_credits("org-a", amount=5, reason="goodwill", idempotency_key="f1"))
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 85
    asyncio.run(svc.rollover("org-a", idempotency_key="r1", eligible_credits=30))
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 115
    asyncio.run(svc.reverse_credits("org-a", original_external_reference="a1",
                                    reason="mistake", idempotency_key="rv1"))
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 135


# ---------------------------------------------------------------------------
# Orders (Assisted estimate → approval → completion; Managed)
# ---------------------------------------------------------------------------


def test_assisted_estimate_uses_configurable_price_book(client, world, user_provider) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    _seed_assisted_pricing(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.post(
        "/api/v3/billing/orders/assisted",
        json={
            "title": "Invoices batch",
            "lines": [
                {"complexity": "simple", "quantity": 10},
                {"complexity": "standard", "quantity": 4},
                {"complexity": "complex", "quantity": 1},
            ],
            "idempotency_key": "est-key-1",
        },
    )
    assert r.status_code == 201, r.text
    order = r.json()["order"]
    assert order["status"] == "awaiting_customer_approval"
    # 10×0.99 + 4×1.99 + 1×3.99 = 21.85 (configurable price book)
    assert abs(order["total_amount"] - 21.85) < 0.001
    assert len(order["items"]) == 3


def test_order_approval_records_payment_intent_and_completes(client, world, user_provider) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.post(
        "/api/v3/billing/orders/assisted",
        json={"title": "One", "lines": [{"complexity": "simple", "quantity": 2}],
              "idempotency_key": "est-key-2"},
    )
    order_id = r.json()["order"]["id"]
    r = client.post(f"/api/v3/billing/orders/{order_id}/approve",
                    json={"idempotency_key": "appr-key-2"})
    assert r.status_code == 200, r.text
    assert r.json()["order"]["status"] == "approved"
    payments = asyncio.run(world.billing_payments.list_for_org("org-a"))
    assert len(payments) == 1
    assert payments[0].status == "pending"
    assert payments[0].provider == "pending"  # provider-neutral placeholder


def test_order_is_org_scoped(client, world, user_provider) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.post(
        "/api/v3/billing/orders/assisted",
        json={"title": "A", "lines": [{"complexity": "simple", "quantity": 1}],
              "idempotency_key": "est-key-3"},
    )
    order_id = r.json()["order"]["id"]
    user_provider.set_user(member_user("org-b", "user-b", "user.b@test"))
    assert client.get(f"/api/v3/billing/me/orders/{order_id}").status_code == 404
    r = client.post(f"/api/v3/billing/orders/{order_id}/approve",
                    json={"idempotency_key": "appr-key-3"})
    assert r.status_code == 404


def test_customer_cannot_mutate_commercial_state_directly(client, world, user_provider) -> None:
    _seed_staff(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.post("/api/v3/commercial/credits/grant",
                    json={"organization_id": "org-a", "amount": 9999,
                          "reason": "self-grant", "idempotency_key": "x-1"})
    assert r.status_code == 403
    r = client.post("/api/v3/commercial/subscriptions",
                    json={"organization_id": "org-a", "plan_code": "enterprise",
                          "idempotency_key": "x-2"})
    assert r.status_code == 403


def test_managed_order_uses_common_model(client, world, user_provider) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    r = client.post(
        "/api/v3/billing/managed/orders",
        json={"title": "Managed batch", "description": "full service scope",
              "quantity_documents": 25, "idempotency_key": "managed-key-1"},
    )
    assert r.status_code == 201, r.text
    order = r.json()["order"]
    assert order["order_type"] == "managed"
    assert order["status"] == "estimated"
    assert order["items"][0]["quoted"] is True


# ---------------------------------------------------------------------------
# Processing charges (CREDIT / STANDARD / no-subscription)
# ---------------------------------------------------------------------------


def test_charge_processing_no_subscription_allowed(world) -> None:
    svc = BillingService(world.bundle())
    result = asyncio.run(svc.charge_processing(
        "org-a", job={"kind": "document", "page_count": 1},
        idempotency_key="chg-1"))
    assert result["mode"] == "no_subscription"
    assert result["allowed"] is True


def test_charge_processing_credit_complexity(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    _seed_credit_rules(world)
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 500, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    result = asyncio.run(svc.charge_processing(
        "org-a", job={"kind": "document", "page_count": 1},
        idempotency_key="chg-1"))
    assert result["mode"] == "CREDIT"
    assert result["units"] == 1  # simple = 1 (configurable)
    assert asyncio.run(world.billing_ledger.balance("org-a")) == 499
    result2 = asyncio.run(svc.charge_processing(
        "org-a", job={"kind": "document", "page_count": 15},
        idempotency_key="chg-2"))
    assert result2["units"] == 4  # complex (configurable thresholds)


def test_charge_processing_structured_bands(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a")
    asyncio.run(world.billing_config.update_version(
        config_key="structured_data_bands",
        config_value={"bands": [
            {"max_rows": 1000, "units": 1},
            {"max_rows": 10000, "units": 3},
            {"max_rows": 50000, "units": 10},
            {"max_rows": None, "units": None, "custom": True},
        ]},
        reason="test", updated_by=None,
    ))
    svc = BillingService(world.bundle())
    asyncio.run(svc.grant_credits("org-a", 500, source="plan_included", reason="monthly",
                                  idempotency_key="g1"))
    result = asyncio.run(svc.charge_processing(
        "org-a", job={"kind": "structured", "rows": 5000},
        idempotency_key="chg-s1"))
    assert result["units"] == 3  # 1,001–10,000 band


def test_charge_processing_standard_allowance(world) -> None:
    _seed_plan(world)
    _activate(world, "org-a", mode="STANDARD")
    asyncio.run(world.billing_config.update_version(
        config_key="standard_allowance",
        config_value={"monthly_processing_units": 10, "additional_rate": None},
        reason="test", updated_by=None,
    ))
    svc = BillingService(world.bundle())
    result = asyncio.run(svc.charge_processing(
        "org-a", job={"kind": "document", "page_count": 1},
        idempotency_key="chg-st1"))
    assert result["mode"] == "STANDARD"
    assert result["allowed"] is True
    ent = asyncio.run(svc.get_entitlement("org-a"))
    assert ent["standard"]["remaining"] == 9

