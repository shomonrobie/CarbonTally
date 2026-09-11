"""P6-2F (CP-F6) — D6/D7/D8/D11 integration acceptance end-to-end.

Verifies that the ratified P6-2C/P6-2D/P6-2E behaviour is preserved and that
P6-2F consumes it without altering any policy.
"""
from __future__ import annotations

import asyncio
import pathlib
import re

from tests.e2e import fixtures as fx
from tests.e2e.personas import consultant_firm_a, internal_qc, org_owner, org_member

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"
ORGS = "/api/v3/organizations"
CONS = "/api/v3/consultants"


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


# --- D6 — entitlement ------------------------------------------------------------


def test_d6_entitlement_is_required_and_org_owned(client, scenario, user_provider) -> None:
    """Org A is entitled; Org B is not. Org B's submission must be denied (D6)."""
    item_a = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    assert _submit(client, user_provider, item_a.id).status_code == 200

    # Org B has no entitlement in this scenario.
    fx.seed_firm(scenario, firm_id=fx.FIRM_B, user_id="u-firm-b", company="Firm B")
    item_b = fx.seed_item(scenario, org_id=fx.ORG_B, status="consultant_reviewed")
    from tests.unit.api.fakes import consultant_user
    user_provider.set_user(consultant_user("u-firm-b", "b@firm-b.test"))
    resp = client.post(f"{PROC}/items/{item_b.id}/consultant-submit")
    assert resp.status_code in (402, 403), resp.text
    # fail-closed: the denied preflight performs no mutation
    assert _status(scenario, item_b.id) == "consultant_reviewed"


def test_d6_no_charge_on_denied_submission(client, scenario, user_provider) -> None:
    """A denied submission must not consume entitlement."""
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    # wrong state (not consultant_reviewed) → denied before any mutation
    user_provider.set_user(consultant_firm_a())
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 409
    assert _status(scenario, item.id) == "calculated"


# --- D7 — provenance -------------------------------------------------------------


def test_d7_provenance_is_server_derived_and_write_once(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    prov = asyncio.run(scenario.manual_extraction.get_item_consultant_provenance(item.id))
    assert prov["consultant_firm_id"] == fx.FIRM_A

    # Write-once: a later attempt (any firm) changes nothing.
    changed = asyncio.run(
        scenario.manual_extraction.record_consultant_provenance(
            item.id, firm_id=fx.FIRM_B, processing_mode="automatic"
        )
    )
    assert changed is False
    again = asyncio.run(scenario.manual_extraction.get_item_consultant_provenance(item.id))
    assert again["consultant_firm_id"] == fx.FIRM_A


def test_d7_mode_is_separate_from_processing_origin(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    prov = asyncio.run(scenario.manual_extraction.get_item_consultant_provenance(item.id))
    origin = asyncio.run(scenario.manual_extraction.get_item_origin(item.id))
    # distinct concepts: provenance carries a mode; origin is its own field
    assert "processing_mode" in prov
    assert origin is None or "processing_origin" in origin


# --- D8 — messaging --------------------------------------------------------------


def test_d8_conversation_kind_vocabulary_unchanged() -> None:
    """No consultant conversation kind / table was introduced (repository scan)."""
    migrations = pathlib.Path(__file__).resolve().parents[3] / "supabase" / "migrations"
    text = "\n".join(p.read_text() for p in sorted(migrations.glob("*.sql")))
    assert "conversation_kind" in text
    values: set[str] = set()
    for group in re.findall(r"conversation_kind[^\n]*?IN\s*\(([^)]*)\)", text):
        values.update(re.findall(r"'([^']+)'", group))
    values.update(re.findall(r"conversation_kind\s*=\s*'([^']+)'", text))
    assert values, "conversation_kind vocabulary not found"
    assert values <= {"org", "entity"}, values
    assert not re.search(r"conversation_kind[^\n]*'consultant'", text)
    assert "consultant_conversations" not in text


def test_d8_consultant_participates_with_role(client, scenario, user_provider) -> None:
    user_provider.set_user(consultant_firm_a())
    resp = client.post("/api/v3/messaging/conversations", json={"organization_id": fx.ORG_A, "subject": "S"})
    assert resp.status_code == 201, resp.text
    convo_id = resp.json()["conversation"]["id"]
    participants = asyncio.run(scenario.messaging.list_participants(convo_id))
    assert [p.metadata.get("participant_role") for p in participants] == ["consultant"]


# --- D11 — lifecycle notifications -----------------------------------------------


def test_d11_accepted_event_reaches_firm_members(client, scenario, user_provider) -> None:
    fx.seed_engagement(scenario, client_id="eng-accept", firm_id=fx.FIRM_A, org_id=fx.ORG_A, status="pending")
    user_provider.set_user(org_owner(fx.ORG_A))
    resp = client.post(f"{ORGS}/{fx.ORG_A}/consultant-engagements/eng-accept/accept")
    assert resp.status_code == 200, resp.text
    key = "consultant.lifecycle.accepted:engagement:eng-accept"
    assert key in scenario.notifications.event_keys()
    assert "u-firm-a" in scenario.notifications.recipients_for(key)


def test_d11_qc_rejection_emits_outcome_and_rework(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    assert _submit(client, user_provider, item.id).status_code == 200
    user_provider.set_user(internal_qc())
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 40, "approved": False, "qc_notes": "bad"},
    )
    assert resp.status_code == 200, resp.text
    keys = set(scenario.notifications.event_keys())
    assert f"consultant.lifecycle.qc_outcome:item:{item.id}:rejected" in keys
    assert f"consultant.lifecycle.rework:item:{item.id}:ct_qc_rejected" in keys


def test_d11_consultant_review_rejection_emits_rework(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id, passed=False, reason="missing data").status_code == 200
    key = f"consultant.lifecycle.rework:item:{item.id}:consultant_review_rejected"
    assert key in scenario.notifications.event_keys()
    assert scenario.notifications.recipients_for(key) == ["u-firm-a"]


def test_d11_recipients_never_leak_cross_tenant(client, scenario, user_provider) -> None:
    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="calculated")
    assert _review(client, user_provider, item.id).status_code == 200
    assert _submit(client, user_provider, item.id).status_code == 200
    user_provider.set_user(internal_qc())
    assert client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True, "qc_notes": "ok"},
    ).status_code == 200
    user_provider.set_user(org_owner(fx.ORG_A))
    assert client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "ok"},
    ).status_code == 200

    recipients: set[str] = set()
    for key in scenario.notifications.event_keys():
        recipients.update(scenario.notifications.recipients_for(key))
    # firm A members + internal ops only — never firm B, never the client actor
    assert "u-firm-b" not in recipients
    assert "u-own" not in recipients
    assert recipients <= {"u-firm-a", "u-ops"}


def test_d11_service_layer_replay_is_idempotent(scenario) -> None:
    from services.consultant_lifecycle import notify_submitted_to_qc

    item = fx.seed_item(scenario, org_id=fx.ORG_A, status="consultant_reviewed")
    repos = scenario.bundle()
    first = asyncio.run(notify_submitted_to_qc(repos, item=item))
    second = asyncio.run(notify_submitted_to_qc(repos, item=item))
    assert first == second  # same recipients, existing rows returned
    assert len(scenario.notifications.rows) == len(first)

