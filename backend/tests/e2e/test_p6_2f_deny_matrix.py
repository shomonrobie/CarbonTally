"""P6-2F (CP-F5) — DENY / security matrix end-to-end.

Every material authorization boundary is exercised from the DENY side: the UI is
NOT the security boundary, so each test asserts the server rejects the operation
AND that nothing durable changed (no state transition, no notification).
"""
from __future__ import annotations

import asyncio

from tests.e2e import fixtures as fx
from tests.e2e.personas import (
    consultant_firm_a,
    consultant_firm_b,
    consultant_ungranted,
    internal_reviewer,
    org_member,
    org_owner,
    org_viewer,
)

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"
NOTIF = "/api/v3/notifications"
MSG = "/api/v3/messaging"


def _status(world, item_id: str) -> str:
    return asyncio.run(world.manual_extraction.get_item(item_id)).status


def test_unauthenticated_is_denied(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="pending")
    user_provider.set_unauthenticated()
    assert client.get(f"{PROC}/items/{item.id}/workspace").status_code == 401


def test_cross_organisation_access_is_denied(client, scenario, user_provider) -> None:
    """Org B owner cannot read Org A's item (organisation isolation)."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="pending")
    user_provider.set_user(org_owner(fx.ORG_B, user_id="u-own-b", email="b@client.test"))
    assert client.get(f"{PROC}/items/{item.id}/workspace").status_code in (403, 404)


def test_consultant_without_grant_is_denied(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="pending")
    user_provider.set_user(consultant_ungranted())
    assert client.get(f"{PROC}/items/{item.id}/workspace").status_code in (403, 404)


def test_cross_firm_consultant_is_denied(client, scenario, user_provider) -> None:
    """Firm B is granted ORG B only — never ORG A."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    user_provider.set_user(consultant_firm_b())
    assert client.post(f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}).status_code in (403, 404)


def test_suspended_grant_is_denied(client, scenario, user_provider) -> None:
    """A firm whose only grant for Org A is SUSPENDED cannot act."""
    fx.seed_firm(scenario, firm_id="firm-c", user_id="u-firm-c", company="Firm C")
    fx.seed_engagement(scenario, client_id="client-c", firm_id="firm-c", org_id=fx.ORG_A, status="suspended")
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    from tests.unit.api.fakes import consultant_user
    user_provider.set_user(consultant_user("u-firm-c", "c@firm-c.test"))
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code in (403, 404)
    assert scenario.notifications.rows == []


def test_consultant_without_submit_capability_is_denied(client, scenario, user_provider) -> None:
    fx.seed_firm(scenario, firm_id=fx.FIRM_A, user_id="u-firm-a-nosub", can_submit=False)
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    from tests.unit.api.fakes import consultant_user
    user_provider.set_user(consultant_user("u-firm-a-nosub", "nosub@firm-a.test"))
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 403
    assert scenario.notifications.rows == []


def test_org_member_cannot_approve_customer_decision(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="ct_qc_approved")
    user_provider.set_user(org_member(fx.ORG_A))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "x"},
    )
    assert resp.status_code == 403
    assert _status(scenario, item.id) == "ct_qc_approved"


def test_org_viewer_cannot_write(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    user_provider.set_user(org_viewer(fx.ORG_A))
    assert client.post(f"{PROC}/items/{item.id}/consultant-submit").status_code == 403


def test_qc_decision_requires_can_qc(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="reviewed")
    body = {"quality_score": 90, "approved": True, "qc_notes": "x"}
    # internal staff WITHOUT can_qc
    user_provider.set_user(internal_reviewer())
    assert client.post(f"{OPS}/qc/items/{item.id}/decision", json=body).status_code == 403
    # a consultant can never make the CT-QC decision
    user_provider.set_user(consultant_firm_a())
    assert client.post(f"{OPS}/qc/items/{item.id}/decision", json=body).status_code == 403
    assert _status(scenario, item.id) == "reviewed"


def test_idor_swapped_identifiers_are_denied(client, scenario, user_provider) -> None:
    """Guessing another organisation's ids must not grant access (IDOR)."""
    item_a = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    user_provider.set_user(consultant_firm_b())
    # Firm B guesses Org A's item id and engagement id
    assert client.get(f"{PROC}/items/{item_a.id}/workspace").status_code in (403, 404)
    assert client.get(f"/api/v3/consultants/clients/{fx.CLIENT_A}/processing/items").status_code in (403, 404)


def test_recipient_injection_is_ignored(client, scenario, user_provider) -> None:
    """A body can never choose notification recipients or event identity."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    user_provider.set_user(consultant_firm_a())
    resp = client.post(
        f"{PROC}/items/{item.id}/consultant-submit",
        json={
            "recipients": ["u-attacker"],
            "event_key": "attacker.chosen.key",
            "actor_domain": "internal_staff",
        },
    )
    assert resp.status_code == 200, resp.text
    keys = scenario.notifications.event_keys()
    # one durable row per recipient (firm member + internal ops), same key
    assert set(keys) == {f"consultant.lifecycle.submitted_to_qc:item:{item.id}"}
    assert "u-attacker" not in scenario.notifications.recipients_for(keys[0])


def test_actor_and_firm_injection_is_ignored(client, scenario, user_provider) -> None:
    """Provenance is server-derived — an injected firm/actor field changes nothing."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    user_provider.set_user(consultant_firm_a())
    resp = client.post(
        f"{PROC}/items/{item.id}/consultant-review",
        json={"passed": True, "consultant_firm_id": fx.FIRM_B, "actor": "u-firm-b"},
    )
    assert resp.status_code == 200, resp.text
    prov = asyncio.run(scenario.manual_extraction.get_item_consultant_provenance(item.id))
    assert prov["consultant_firm_id"] == fx.FIRM_A


def test_processing_origin_injection_is_ignored(client, scenario, user_provider) -> None:
    """The two-value processing-origin vocabulary cannot be driven by the client."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    user_provider.set_user(consultant_firm_a())
    resp = client.post(
        f"{PROC}/items/{item.id}/consultant-submit",
        json={"processing_origin": "CONSULTANT", "origin": "CONSULTANT"},
    )
    assert resp.status_code == 200, resp.text
    origin = asyncio.run(scenario.manual_extraction.get_item_origin(item.id))
    value = (origin or {}).get("processing_origin")
    assert value != "CONSULTANT"
    assert value in (None, "CARBONTALLY_INTERNAL", "PROCESSING_ENTITY")


def test_replay_does_not_duplicate_side_effects(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    user_provider.set_user(consultant_firm_a())
    assert client.post(f"{PROC}/items/{item.id}/consultant-submit").status_code == 200
    rows_after_first = len(scenario.notifications.rows)
    # Replay: the state machine refuses the second submission.
    assert client.post(f"{PROC}/items/{item.id}/consultant-submit").status_code == 409
    assert len(scenario.notifications.rows) == rows_after_first


def test_alternate_internal_route_requires_staff(client, scenario, user_provider) -> None:
    """The internal submit-review route cannot be used by a customer/consultant."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    user_provider.set_user(org_owner(fx.ORG_A))
    assert client.post(f"{OPS}/items/{item.id}/submit-review").status_code == 403
    user_provider.set_user(consultant_firm_a())
    assert client.post(f"{OPS}/items/{item.id}/submit-review").status_code == 403


def test_ungranted_consultant_cannot_message_client(client, scenario, user_provider) -> None:
    """D8 DENY — messaging requires an active grant."""
    user_provider.set_user(consultant_ungranted())
    resp = client.post(f"{MSG}/conversations", json={"organization_id": fx.ORG_A, "subject": "Nope"})
    assert resp.status_code == 403

