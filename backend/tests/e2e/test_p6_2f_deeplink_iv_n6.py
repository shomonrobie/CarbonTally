"""P6-2F — IV-N6 carry-forward: consultant notification deep links.

P6-2E emitted ``/consultant/items/{item_id}``, which does not match the real
frontend route ``/consultant/items/:clientId/:itemId``. The fix supplies the
recipient firm's engagement id and the tests assert BOTH the ALLOW (the route
resolves and is authorised for the granted consultant) and the DENY (an
unrelated consultant / other firm cannot use it).
"""
from __future__ import annotations

from tests.e2e import fixtures as fx
from tests.e2e.personas import consultant_firm_a, consultant_firm_b

PROC = "/api/v3/processing"
CONS = "/api/v3/consultants"
OPS = "/api/v3/ops"


def _submit(client, user_provider, item_id: str):
    user_provider.set_user(consultant_firm_a())
    return client.post(f"{PROC}/items/{item_id}/consultant-submit")


def _link_for(world, recipient_id: str) -> str | None:
    for row in world.notifications.rows:
        if row["recipient_id"] == recipient_id:
            return row.get("link")
    return None


def test_deeplink_targets_the_real_consultant_item_route(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    assert _submit(client, user_provider, item.id).status_code == 200

    expected = f"/consultant/items/{fx.CLIENT_A}/{item.id}"
    assert _link_for(scenario, "u-firm-a") == expected
    # The P6-2E item-only shape must not be emitted again.
    assert _link_for(scenario, "u-firm-a") != f"/consultant/items/{item.id}"


def test_deeplink_route_resolves_for_the_granted_consultant(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    assert _submit(client, user_provider, item.id).status_code == 200

    # Both endpoints the consultant item page calls behind the deep link.
    user_provider.set_user(consultant_firm_a())
    assert client.get(f"{CONS}/clients/{fx.CLIENT_A}/processing/items").status_code == 200
    assert client.get(f"{PROC}/items/{item.id}/workspace").status_code == 200


def test_deeplink_route_is_denied_for_an_unrelated_consultant(client, scenario, user_provider) -> None:
    """Directly navigating the deep-link route as another firm is denied."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    assert _submit(client, user_provider, item.id).status_code == 200

    user_provider.set_user(consultant_firm_b())
    assert client.get(f"{CONS}/clients/{fx.CLIENT_A}/processing/items").status_code in (403, 404)
    assert client.get(f"{PROC}/items/{item.id}/workspace").status_code in (403, 404)


def test_internal_recipient_link_is_a_valid_route(client, scenario, user_provider) -> None:
    """Non-firm recipients (internal ops) get a valid route, never a broken path."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    assert _submit(client, user_provider, item.id).status_code == 200
    assert _link_for(scenario, "u-ops") == "/notifications"
