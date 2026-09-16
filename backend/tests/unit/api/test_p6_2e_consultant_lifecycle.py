"""P6-2E — Consultant vocabulary (D8) and lifecycle events (D11).

Ratified: ``PO-PHASE6-D11-20260910`` / ``PO-PHASE6-D8-20260910``; contract
``CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`` §7.

D11 — the five consultant lifecycle events are emitted as durable, idempotent
notifications (existing ``notifications`` table + ``create_idempotent``), with
deterministic server-generated event keys and server-derived recipients:

    accepted | submitted_to_qc | qc_outcome | customer_decision | rework

D8 — the existing conversation model is reused unchanged: consultants
participate through active client grants with participant role ``consultant``,
``conversation_kind`` remains the existing ``org``/``entity`` vocabulary, and
no consultant-specific conversation kind/table exists.

Every negative case asserts BOTH the HTTP outcome and that no event was
produced (a denied action must never notify).
"""
from __future__ import annotations

import asyncio
import pathlib
import re
import uuid

import pytest

from datetime import datetime, timezone

from domain.billing import BillingPlan, Subscription
from domain.staff import StaffProfile, StaffRole
from services.billing import BillingService
from services.consultant_lifecycle import (
    CONSULTANT_LIFECYCLE_EVENTS,
    EVENT_ACCEPTED,
    EVENT_CUSTOMER_DECISION,
    EVENT_QC_OUTCOME,
    EVENT_REWORK,
    EVENT_SUBMITTED_TO_QC,
    NOTIFICATION_TYPE,
    REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED,
    REWORK_SOURCE_CT_QC_REJECTED,
    lifecycle_event_key,
)
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_admin_user,
    org_owner_user,
    staff_user,
)

CONSULTANTS = "/api/v3/consultants"
ORGS = "/api/v3/organizations"
PROC = "/api/v3/processing"
OPS = "/api/v3/ops"
MSG = "/api/v3/messaging"

FIRM = "firm-c1"


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------


def _seed_firm(
    world,
    *,
    firm_id: str = FIRM,
    user_id: str = "u-c1",
    role: str = "manager",
    is_active: bool = True,
    **flags,
):
    """Seed a consultant firm + one member (capabilities opt-in)."""
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role=role,
        is_active=is_active,
        can_manage_clients=flags.get("can_manage_clients", True),
        can_submit=flags.get("can_submit", True),
        can_extract=flags.get("can_extract", False),
        can_map=flags.get("can_map", False),
        can_validate=flags.get("can_validate", False),
        can_calculate=flags.get("can_calculate", False),
    )
    return consultant_user(user_id, f"{user_id}@example.test", role=role)


def _seed_grant(
    world,
    *,
    client_id: str = "cc-1",
    firm_id: str = FIRM,
    org_id: str = "org-a",
    status: str = "active",
):
    # FIN-06 precondition: manual processing is enabled for the client org.
    world.manual_processing.seed_grant("organization", org_id)
    return world.consultants.seed_client(
        client_id,
        firm_id,
        org_id,
        "Client Org",
        status=status,
        relationship_origin="consultant_created_customer",
    )


def _seed_item(
    world, *, org_id: str = "org-a", status: str = "consultant_reviewed", item_id=None
):
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}",
        org_id,
        "invoice.pdf",
        status=status,
    )


def _seed_commercial(world, org_id: str = "org-a", *, key: str | None = None) -> None:
    key = key or f"sub-{uuid.uuid4().hex[:8]}"
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()),
                plan_code="professional",
                name="Professional",
                price=149,
                currency="GBP",
                included_credits=500,
                version=1,
                is_active=True,
                features={},
                effective_from=datetime.now(timezone.utc),
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                plan_code="professional",
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
    asyncio.run(
        BillingService(world.bundle()).grant_credits(
            org_id,
            500,
            source="plan_included",
            reason="monthly",
            idempotency_key=f"{key}-grant",
        )
    )


def _seed_qc_staff(world, *, user_id: str = "u-qc") -> None:
    world.staff.seed_role(
        StaffRole(id="role-qc", name="qc_specialist", permissions={"can_qc": True})
    )
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name=user_id,
            last_name="One",
            email=f"{user_id}@test",
            role_id="role-qc",
            entity_id=None,
        )
    )


def _seed_ops_staff(world, *, user_id: str = "u-ops") -> None:
    """Internal staff whose role grants ``can_manage_staff`` (existing resolver)."""
    world.staff.seed_role(
        StaffRole(
            id="role-ops",
            name="support_admin",
            permissions={"can_manage_staff": True},
        )
    )
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name=user_id,
            last_name="Ops",
            email=f"{user_id}@test",
            role_id="role-ops",
            entity_id=None,
        )
    )


def _keys(world) -> list[str]:
    return world.notifications.event_keys()


def _rows(world) -> list[dict]:
    return world.notifications.rows


def _keys_of(world, notification_type: str) -> list[str]:
    return world.notifications.event_keys_of_type(notification_type)


def _recipients(world, event_key: str) -> list[str]:
    return world.notifications.recipients_for(event_key)


def _submit(client, world, user_provider, item):
    """Consultant submits a ``consultant_reviewed`` item → ``reviewed``."""
    user = _seed_firm(world)
    _seed_grant(world)
    _seed_commercial(world)
    user_provider.set_user(user)
    return client.post(f"{PROC}/items/{item.id}/consultant-submit")


def _qc_decision(client, world, user_provider, item_id, *, approved=True, score=90):
    _seed_qc_staff(world)
    user_provider.set_user(staff_user("u-qc"))
    return client.post(
        f"{OPS}/qc/items/{item_id}/decision",
        json={"quality_score": score, "approved": approved, "qc_notes": "checked"},
    )




# ---------------------------------------------------------------------------
# Event 1 — accepted (client accepts the consultant engagement)
# ---------------------------------------------------------------------------


def _seed_pending_engagement(world, *, org_id="org-a", engagement_id="eng-1"):
    world.organizations.seed_org(org_id, name="Client Org")
    _seed_firm(world)
    _seed_grant(world, client_id=engagement_id, org_id=org_id, status="pending")


def test_engagement_accepted_emits_lifecycle_event_for_firm_members(
    client, world, user_provider
) -> None:
    _seed_pending_engagement(world)
    # A second ACTIVE firm member, an INACTIVE member and an unrelated firm.
    _seed_firm(world, user_id="u-c2")
    _seed_firm(world, user_id="u-off", is_active=False)
    _seed_firm(world, firm_id="firm-other", user_id="u-other")

    user_provider.set_user(org_owner_user("org-a", "u-own", "owner@client.test"))
    resp = client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept")
    assert resp.status_code == 200, resp.text

    key = "consultant.lifecycle.accepted:engagement:eng-1"
    assert _keys(world) == [key, key]  # one durable row per ACTIVE firm member
    assert _recipients(world, key) == ["u-c1", "u-c2"]  # inactive/other excluded
    assert _keys_of(world, NOTIFICATION_TYPE[EVENT_ACCEPTED]) == [key, key]
    assert _rows(world)[0]["actor_domain"] == "organisation_member"


def test_engagement_accept_denied_paths_emit_nothing(client, world, user_provider) -> None:
    _seed_pending_engagement(world)
    # (a) org MEMBER cannot accept.
    user_provider.set_user(member_user("org-a", "u-mem", "m@client.test"))
    assert client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept").status_code == 403
    # (b) a DIFFERENT org admin cannot accept.
    user_provider.set_user(org_admin_user("org-other", "u-oth", "o@test"))
    assert client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept").status_code == 403
    # (c) unauthenticated.
    user_provider.set_unauthenticated()
    assert client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept").status_code == 401
    assert _rows(world) == []


def test_engagement_accept_replay_emits_no_additional_event(
    client, world, user_provider
) -> None:
    _seed_pending_engagement(world)
    user_provider.set_user(org_owner_user("org-a", "u-own", "owner@client.test"))
    assert client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept").status_code == 200
    first = len(_rows(world))
    assert first > 0
    # Replay of the same acceptance: 409 and no additional events.
    assert client.post(f"{ORGS}/org-a/consultant-engagements/eng-1/accept").status_code == 409
    assert len(_rows(world)) == first
    # Deterministic key ⇒ one durable row per recipient.
    key = "consultant.lifecycle.accepted:engagement:eng-1"
    recips = _recipients(world, key)
    assert len(recips) == len(set(recips))


# ---------------------------------------------------------------------------
# Event 2 — submitted_to_qc
# ---------------------------------------------------------------------------


def test_submission_emits_deterministic_submitted_event(client, world, user_provider) -> None:
    item = _seed_item(world)
    resp = _submit(client, world, user_provider, item)
    assert resp.status_code == 200, resp.text

    key = f"consultant.lifecycle.submitted_to_qc:item:{item.id}"
    assert _keys(world) == [key]
    assert _recipients(world, key) == ["u-c1"]
    assert _keys_of(world, NOTIFICATION_TYPE[EVENT_SUBMITTED_TO_QC]) == [key]
    assert _rows(world)[0]["actor_domain"] == "consultant"


def test_submission_notifies_internal_ops_recipients(client, world, user_provider) -> None:
    """QC-intake visibility uses the EXISTING internal ops resolver."""
    _seed_ops_staff(world, user_id="u-ops")
    item = _seed_item(world)
    resp = _submit(client, world, user_provider, item)
    assert resp.status_code == 200, resp.text
    key = f"consultant.lifecycle.submitted_to_qc:item:{item.id}"
    assert _recipients(world, key) == ["u-c1", "u-ops"]


def test_submission_without_capability_emits_nothing(client, world, user_provider) -> None:
    item = _seed_item(world)
    _seed_firm(world, can_submit=False)
    _seed_grant(world)
    _seed_commercial(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    assert client.post(f"{PROC}/items/{item.id}/consultant-submit").status_code == 403
    assert _rows(world) == []


def test_submission_state_grant_and_auth_denials_emit_nothing(
    client, world, user_provider
) -> None:
    """Denied classes: state conflict, no active grant, unauthenticated."""
    user = _seed_firm(world)
    _seed_grant(world)
    _seed_commercial(world)
    user_provider.set_user(user)
    # (a) wrong workflow state (`calculated` is not submittable).
    item = _seed_item(world, status="calculated")
    assert client.post(f"{PROC}/items/{item.id}/consultant-submit").status_code == 409
    # (b) a SUSPENDED grant cannot submit.
    world.consultants.seed_client("cc-2", FIRM, "org-b", "Other", status="suspended")
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    item2 = _seed_item(world, org_id="org-b")
    assert client.post(f"{PROC}/items/{item2.id}/consultant-submit").status_code == 403
    # (c) unauthenticated.
    item3 = _seed_item(world)
    user_provider.set_unauthenticated()
    assert client.post(f"{PROC}/items/{item3.id}/consultant-submit").status_code == 401
    assert _rows(world) == []


def test_submission_replay_emits_one_durable_event(client, world, user_provider) -> None:
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    first = len(_rows(world))
    assert first == 1
    # A second submission of the same item is refused (state conflict) and the
    # already-persisted event is not duplicated.
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 409
    assert len(_rows(world)) == first


def test_internal_submit_review_is_not_a_consultant_lifecycle_event(
    client, world, user_provider
) -> None:
    """Alternate route protection: internal `submit-review` emits no D11 event."""
    world.staff.seed_role(
        StaffRole(id="role-rev", name="reviewer", permissions={"can_review": True})
    )
    world.staff.seed_profile(
        StaffProfile(
            id="sp-u-rev",
            user_id="u-rev",
            first_name="rev",
            last_name="One",
            email="u-rev@test",
            role_id="role-rev",
            entity_id=None,
        )
    )
    item = _seed_item(world, status="calculated")
    user_provider.set_user(staff_user("u-rev"))
    resp = client.post(f"{OPS}/items/{item.id}/submit-review")
    assert resp.status_code == 200, resp.text
    assert _rows(world) == []


# ---------------------------------------------------------------------------
# Event 3 (+5) — qc_outcome and rework
# ---------------------------------------------------------------------------


def test_qc_approval_emits_outcome_event_for_firm_only(client, world, user_provider) -> None:
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    before = len(_rows(world))
    resp = _qc_decision(client, world, user_provider, item.id, approved=True)
    assert resp.status_code == 200, resp.text

    key = f"consultant.lifecycle.qc_outcome:item:{item.id}:approved"
    assert _keys(world)[before:] == [key]
    assert _recipients(world, key) == ["u-c1"]
    assert _rows(world)[-1]["actor_domain"] == "internal_staff"
    # The QC actor (internal staff) is never a recipient of their own decision.
    assert "u-qc" not in _recipients(world, key)
    # Approval has no rework event.
    assert _keys_of(world, NOTIFICATION_TYPE[EVENT_REWORK]) == []


def test_qc_rejection_emits_outcome_and_rework(client, world, user_provider) -> None:
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    resp = _qc_decision(client, world, user_provider, item.id, approved=False)
    assert resp.status_code == 200, resp.text

    outcome = f"consultant.lifecycle.qc_outcome:item:{item.id}:rejected"
    rework = f"consultant.lifecycle.rework:item:{item.id}:{REWORK_SOURCE_CT_QC_REJECTED}"
    assert _keys(world) == [
        f"consultant.lifecycle.submitted_to_qc:item:{item.id}",
        outcome,
        rework,
    ]
    assert _recipients(world, outcome) == ["u-c1"]
    assert _recipients(world, rework) == ["u-c1"]


def test_qc_decision_denied_paths_emit_nothing(client, world, user_provider) -> None:
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    before = len(_rows(world))
    # (a) internal staff WITHOUT can_qc.
    world.staff.seed_role(StaffRole(id="role-noop", name="operator", permissions={}))
    world.staff.seed_profile(
        StaffProfile(
            id="sp-u-noop",
            user_id="u-noop",
            first_name="no",
            last_name="Qc",
            email="u-noop@test",
            role_id="role-noop",
            entity_id=None,
        )
    )
    user_provider.set_user(staff_user("u-noop"))
    assert client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True, "qc_notes": "x"},
    ).status_code == 403
    # (b) unauthenticated.
    user_provider.set_unauthenticated()
    assert client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True, "qc_notes": "x"},
    ).status_code == 401
    # (c) a consultant can never make the CT-QC decision.
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    assert client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True, "qc_notes": "x"},
    ).status_code == 403
    assert len(_rows(world)) == before


def test_qc_decision_replay_emits_no_duplicate(client, world, user_provider) -> None:
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    assert _qc_decision(client, world, user_provider, item.id, approved=True).status_code == 200
    first = len(_rows(world))
    # Replay: the item is no longer in CT-QC intake → 409, no event.
    assert _qc_decision(client, world, user_provider, item.id, approved=True).status_code == 409
    assert len(_rows(world)) == first


# ---------------------------------------------------------------------------
# Event 4 — customer_decision
# ---------------------------------------------------------------------------


def _seed_ct_qc_approved(client, world, user_provider):
    item = _seed_item(world)
    assert _submit(client, world, user_provider, item).status_code == 200
    assert _qc_decision(client, world, user_provider, item.id, approved=True).status_code == 200
    return item


def _customer_review(client, item_id, *, approved: bool):
    return client.post(
        f"{PROC}/items/{item_id}/customer-review",
        json={
            "approved": approved,
            "rejection_reason": None if approved else "no",
            "customer_notes": "t",
        },
    )


def test_customer_approval_emits_decision_event_for_firm(client, world, user_provider) -> None:
    item = _seed_ct_qc_approved(client, world, user_provider)
    before = len(_rows(world))
    user_provider.set_user(org_owner_user("org-a", "u-own", "owner@client.test"))
    resp = _customer_review(client, item.id, approved=True)
    assert resp.status_code == 200, resp.text

    key = f"consultant.lifecycle.customer_decision:item:{item.id}:approved"
    assert _keys(world)[before:] == [key]
    assert _recipients(world, key) == ["u-c1"]
    assert _rows(world)[-1]["actor_domain"] == "organisation_member"
    # The client actor is not notified of its own decision.
    assert "u-own" not in _recipients(world, key)


def test_customer_rejection_emits_decision_event_only(client, world, user_provider) -> None:
    item = _seed_ct_qc_approved(client, world, user_provider)
    user_provider.set_user(org_owner_user("org-a", "u-own", "owner@client.test"))
    resp = _customer_review(client, item.id, approved=False)
    assert resp.status_code == 200, resp.text
    key = f"consultant.lifecycle.customer_decision:item:{item.id}:rejected"
    assert key in _keys(world)
    assert _recipients(world, key) == ["u-c1"]
    # Only the governed CT-QC rejection produces a rework event.
    assert _keys_of(world, NOTIFICATION_TYPE[EVENT_REWORK]) == []


def test_customer_decision_denied_paths_emit_nothing(client, world, user_provider) -> None:
    item = _seed_ct_qc_approved(client, world, user_provider)
    before = len(_rows(world))
    # (a) org member (not owner/admin) cannot decide.
    user_provider.set_user(member_user("org-a", "u-mem", "m@client.test"))
    assert _customer_review(client, item.id, approved=True).status_code == 403
    # (b) another organisation's owner cannot decide.
    user_provider.set_user(org_owner_user("org-b", "u-other", "o@test"))
    assert _customer_review(client, item.id, approved=True).status_code in (403, 404)
    # (c) consultant cannot decide.
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    assert _customer_review(client, item.id, approved=True).status_code == 403
    # (d) unauthenticated.
    user_provider.set_unauthenticated()
    assert _customer_review(client, item.id, approved=True).status_code == 401
    assert len(_rows(world)) == before


# ---------------------------------------------------------------------------
# Event 5 — rework (consultant-review rejection)
# ---------------------------------------------------------------------------


def test_consultant_review_rejection_emits_rework_event(client, world, user_provider) -> None:
    item = _seed_item(world, status="calculated")
    user = _seed_firm(world)
    _seed_grant(world)
    user_provider.set_user(user)
    resp = client.post(
        f"{PROC}/items/{item.id}/consultant-review",
        json={"passed": False, "rejection_reason": "wrong quantity"},
    )
    assert resp.status_code == 200, resp.text
    key = f"consultant.lifecycle.rework:item:{item.id}:{REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED}"
    assert _keys(world) == [key]
    assert _recipients(world, key) == ["u-c1"]
    assert _rows(world)[0]["actor_domain"] == "consultant"


def test_consultant_review_pass_and_denial_emit_nothing(client, world, user_provider) -> None:
    item = _seed_item(world, status="calculated")
    user = _seed_firm(world)
    _seed_grant(world)
    user_provider.set_user(user)
    # (a) a PASSED review is not a rework event.
    assert client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    ).status_code == 200
    assert _rows(world) == []
    # (b) a denied review (org member, not a consultant) emits nothing.
    item2 = _seed_item(world, status="calculated")
    user_provider.set_user(member_user("org-a", "u-mem", "m@client.test"))
    assert client.post(
        f"{PROC}/items/{item2.id}/consultant-review",
        json={"passed": False, "rejection_reason": "x"},
    ).status_code == 403
    assert _rows(world) == []


# ---------------------------------------------------------------------------
# Recipients — server-derived only; cross-org / cross-firm isolation
# ---------------------------------------------------------------------------


def test_recipients_are_server_derived_and_body_injection_is_ignored(
    client, world, user_provider
) -> None:
    """A request body can never choose recipients or the event identity."""
    item = _seed_item(world)
    user = _seed_firm(world)
    _seed_grant(world)
    _seed_commercial(world)
    user_provider.set_user(user)
    resp = client.post(
        f"{PROC}/items/{item.id}/consultant-submit",
        json={
            "recipients": ["u-attacker"],
            "event_key": "attacker.chosen.key",
            "actor_domain": "internal_staff",
        },
    )
    assert resp.status_code == 200, resp.text
    assert _keys(world) == [f"consultant.lifecycle.submitted_to_qc:item:{item.id}"]
    assert _recipients(world, _keys(world)[0]) == ["u-c1"]
    assert "u-attacker" not in _recipients(world, _keys(world)[0])


def test_cross_firm_and_cross_org_recipients_are_excluded(client, world, user_provider) -> None:
    """Only the firm engaged for THIS organisation is notified."""
    item = _seed_item(world)
    user = _seed_firm(world)  # firm-c1 / u-c1 — holds the ORG-A grant
    _seed_grant(world)  # cc-1 → firm-c1 / org-a (active)
    _seed_firm(world, firm_id="firm-c2", user_id="u-c2")  # another firm
    _seed_grant(world, client_id="cc-2", firm_id="firm-c2", org_id="org-b")
    _seed_commercial(world)
    user_provider.set_user(user)
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 200, resp.text
    key = f"consultant.lifecycle.submitted_to_qc:item:{item.id}"
    # Only the org-a firm's member; the org-b firm is never a recipient.
    assert _recipients(world, key) == ["u-c1"]


def test_no_active_grant_means_no_firm_recipients(client, world, user_provider) -> None:
    """A suspended grant yields zero firm recipients (and never the staff actor)."""
    _seed_firm(world)
    _seed_grant(world, status="suspended")
    item = _seed_item(world)
    _seed_commercial(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code in (403, 404)
    assert _rows(world) == []


# ---------------------------------------------------------------------------
# Idempotency / event-key design (durable layer semantics)
# ---------------------------------------------------------------------------


def test_service_replay_persists_exactly_one_row_per_recipient(world) -> None:
    from services.consultant_lifecycle import notify_submitted_to_qc

    _seed_firm(world)
    _seed_grant(world)
    item = _seed_item(world)
    repos = world.bundle()
    assert asyncio.run(notify_submitted_to_qc(repos, item=item)) == ["u-c1"]
    assert asyncio.run(notify_submitted_to_qc(repos, item=item)) == ["u-c1"]
    assert len(world.notifications.rows) == 1


def test_lifecycle_event_key_is_deterministic_and_server_generated() -> None:
    key = lifecycle_event_key(EVENT_ACCEPTED, identity="engagement:eng-1")
    assert key == "consultant.lifecycle.accepted:engagement:eng-1"
    assert key == lifecycle_event_key(EVENT_ACCEPTED, identity="engagement:eng-1")
    assert lifecycle_event_key(EVENT_SUBMITTED_TO_QC, identity="item:1") == (
        "consultant.lifecycle.submitted_to_qc:item:1"
    )
    # Outcomes / rework sources are DISTINCT events with distinct keys.
    assert lifecycle_event_key(
        EVENT_QC_OUTCOME, identity="item:1", discriminator="approved"
    ) != lifecycle_event_key(EVENT_QC_OUTCOME, identity="item:1", discriminator="rejected")
    assert lifecycle_event_key(
        EVENT_REWORK, identity="item:1", discriminator=REWORK_SOURCE_CT_QC_REJECTED
    ) != lifecycle_event_key(
        EVENT_REWORK,
        identity="item:1",
        discriminator=REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED,
    )
    assert lifecycle_event_key(
        EVENT_ACCEPTED, identity="engagement:1"
    ) != lifecycle_event_key(EVENT_ACCEPTED, identity="engagement:2")
    with pytest.raises(ValueError):
        lifecycle_event_key("not-a-lifecycle-event", identity="x")


def test_lifecycle_vocabulary_is_exactly_the_five_ratified_events() -> None:
    assert CONSULTANT_LIFECYCLE_EVENTS == (
        "accepted",
        "submitted_to_qc",
        "qc_outcome",
        "customer_decision",
        "rework",
    )
    assert set(NOTIFICATION_TYPE.values()) == {
        "consultant.lifecycle.accepted",
        "consultant.lifecycle.submitted_to_qc",
        "consultant.lifecycle.qc_outcome",
        "consultant.lifecycle.customer_decision",
        "consultant.lifecycle.rework",
    }


# ---------------------------------------------------------------------------
# D8 — the EXISTING conversation model is reused (no consultant kind/table)
# ---------------------------------------------------------------------------


def test_consultant_participates_through_existing_conversation_model(
    client, world, user_provider
) -> None:
    """A granted consultant uses the existing org conversation + role."""
    _seed_firm(world)
    _seed_grant(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(
        f"{MSG}/conversations", json={"organization_id": "org-a", "subject": "Kickoff"}
    )
    assert resp.status_code == 201, resp.text
    conversation = resp.json()["conversation"]
    assert conversation["organization_id"] == "org-a"
    participants = asyncio.run(world.messaging.list_participants(conversation["id"]))
    assert [(p.user_id, p.metadata.get("participant_role")) for p in participants] == [
        ("u-c1", "consultant")
    ]


def test_consultant_without_grant_cannot_message_client_org(
    client, world, user_provider
) -> None:
    """Organisation isolation is unchanged: no grant → no conversation."""
    _seed_firm(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(
        f"{MSG}/conversations", json={"organization_id": "org-a", "subject": "Kickoff"}
    )
    assert resp.status_code == 403


def test_no_consultant_conversation_kind_was_introduced() -> None:
    """conversation_kind remains the existing ``org``/``entity`` vocabulary."""
    migrations = pathlib.Path(__file__).resolve().parents[4] / "supabase" / "migrations"
    text = "\n".join(p.read_text() for p in sorted(migrations.glob("*.sql")))
    assert "conversation_kind" in text
    values = set(re.findall(r"conversation_kind\s*=\s*'([^']+)'", text))
    for group in re.findall(r"conversation_kind\s+IN\s*\(([^)]*)\)", text):
        values.update(re.findall(r"'([^']+)'", group))
    assert values, "conversation_kind vocabulary not found in migrations"
    assert values <= {"org", "entity"}, values
    # No consultant value assigned to conversation_kind anywhere.
    assert not re.search(r"conversation_kind[^\n]*'consultant'", text)
    # No consultant conversation table was minted.
    assert "consultant_conversations" not in text






