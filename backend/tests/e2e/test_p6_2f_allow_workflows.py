"""P6-2F (CP-F4) — browser/application ALLOW workflows end-to-end.

Each test drives the real FastAPI app through the representative personas and
asserts the business outcome (state + durable side effects), not just a status
code. This is the ALLOW half of the security matrix.
"""
from __future__ import annotations

import asyncio

from tests.e2e import fixtures as fx
from tests.e2e.personas import (
    consultant_firm_a,
    consultant_firm_b,
    internal_qc,
    org_owner,
)

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"
CONS = "/api/v3/consultants"
NOTIF = "/api/v3/notifications"
MSG = "/api/v3/messaging"


def _status(world, item_id: str) -> str:
    return asyncio.run(world.manual_extraction.get_item(item_id)).status


def _review(client, user_provider, item_id: str, *, passed: bool = True, reason=None):
    user_provider.set_user(consultant_firm_a())
    body = {"passed": passed}
    if reason is not None:
        body["rejection_reason"] = reason
    return client.post(f"{PROC}/items/{item_id}/consultant-review", json=body)


def _submit(client, user_provider, item_id: str):
    user_provider.set_user(consultant_firm_a())
    return client.post(f"{PROC}/items/{item_id}/consultant-submit")


def _qc_decision(client, user_provider, item_id: str, *, approved: bool = True):
    user_provider.set_user(internal_qc())
    return client.post(
        f"{OPS}/qc/items/{item_id}/decision",
        json={"quality_score": 90, "approved": approved, "qc_notes": "checked"},
    )


def _customer_review(client, user_provider, item_id: str, *, approved: bool = True):
    user_provider.set_user(org_owner())
    return client.post(
        f"{PROC}/items/{item_id}/customer-review",
        json={
            "approved": approved,
            "rejection_reason": None if approved else "no",
            "customer_notes": "e2e",
        },
    )


def test_org_owner_reads_own_item_workspace(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="pending")
    user_provider.set_user(org_owner(fx.ORG_A))
    resp = client.get(f"{PROC}/items/{item.id}/workspace")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["item"]["id"] == item.id
    assert body["batch"]["organization_id"] == fx.ORG_A


def test_granted_consultant_reads_client_item_workspace(client, scenario, user_provider) -> None:
    """ALLOW — the consultant workspace route (NOT the internal /ops route)."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    user_provider.set_user(consultant_firm_a())
    resp = client.get(f"{PROC}/items/{item.id}/workspace")
    assert resp.status_code == 200, resp.text

    listed = client.get(f"{CONS}/clients/{fx.CLIENT_A}/processing/items")
    assert listed.status_code == 200, listed.text


def test_consultant_review_pass_records_provenance_and_advances(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    resp = _review(client, user_provider, item.id, passed=True)
    assert resp.status_code == 200, resp.text
    assert _status(scenario, item.id) == "consultant_reviewed"

    prov = asyncio.run(scenario.manual_extraction.get_item_consultant_provenance(item.id))
    assert prov is not None, "D7 provenance must be recorded for a consultant action"
    assert prov["consultant_firm_id"] == fx.FIRM_A  # server-derived, never client-supplied
    assert prov["processing_mode"] in ("manual", "automatic")


def test_submit_to_qc_emits_firm_centric_notification(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    resp = _submit(client, user_provider, item.id)
    assert resp.status_code == 200, resp.text
    assert _status(scenario, item.id) == "reviewed"

    key = f"consultant.lifecycle.submitted_to_qc:item:{item.id}"
    assert key in scenario.notifications.event_keys()
    assert "u-firm-a" in scenario.notifications.recipients_for(key)


def test_qc_approval_emits_outcome_to_firm_only(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    assert _submit(client, user_provider, item.id).status_code == 200
    resp = _qc_decision(client, user_provider, item.id, approved=True)
    assert resp.status_code == 200, resp.text
    assert _status(scenario, item.id) == "ct_qc_approved"

    key = f"consultant.lifecycle.qc_outcome:item:{item.id}:approved"
    assert scenario.notifications.recipients_for(key) == ["u-firm-a"]

def test_customer_approval_emits_decision_to_firm_only(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    assert _submit(client, user_provider, item.id).status_code == 200
    assert _qc_decision(client, user_provider, item.id).status_code == 200
    resp = _customer_review(client, user_provider, item.id, approved=True)
    assert resp.status_code == 200, resp.text
    assert _status(scenario, item.id) == "approved"

    key = f"consultant.lifecycle.customer_decision:item:{item.id}:approved"
    assert scenario.notifications.recipients_for(key) == ["u-firm-a"]
    # D11-C1 — no client-organisation recipient on a D11 lifecycle event.
    assert "u-own" not in scenario.notifications.recipients_for(key)


def test_granted_consultant_can_message_client_org(client, scenario, user_provider) -> None:
    """D8 ALLOW — consultants participate through the existing conversation model."""
    user_provider.set_user(consultant_firm_a())
    resp = client.post(f"{MSG}/conversations", json={"organization_id": fx.ORG_A, "subject": "Kickoff"})
    assert resp.status_code == 201, resp.text
    conversation = resp.json()["conversation"]
    participants = asyncio.run(scenario.messaging.list_participants(conversation["id"]))
    assert [p.user_id for p in participants] == ["u-firm-a"]


def test_notifications_are_recipient_scoped(client, scenario, user_provider) -> None:
    """A user only ever sees their own notifications."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    assert _submit(client, user_provider, item.id).status_code == 200

    user_provider.set_user(consultant_firm_a())
    mine = client.get(NOTIF)
    assert mine.status_code == 200, mine.text
    assert len(mine.json()["notifications"]) >= 1

    user_provider.set_user(consultant_firm_b())
    theirs = client.get(NOTIF)
    assert theirs.status_code == 200, theirs.text
    assert theirs.json()["notifications"] == []

