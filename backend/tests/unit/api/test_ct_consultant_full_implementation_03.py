"""CT-CONSULTANT-PLATFORM-FULL-IMPLEMENTATION-03 — bounded net-new increments.

Binding authority: ``docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md``
(PD-5 = C+S2; PO-1 = existing, operationalised). These tests cover the two
DECISION halves that ``CT-CONSULTANT-PLATFORM-CLOSURE-01`` deliberately left
fail-closed and that the register now unblocks:

* PD-5 — the firm (a party) DECIDES an inbound client relationship change/end
  request; approving an ``end_relationship`` performs a NON-DESTRUCTIVE
  termination (no Organisation/data/history deletion).
* PO-1 — the CarbonTally Admin DECIDES a firm's mode-change request; the ONLY
  writer of ``commercial_mode`` is the admin route.

Everything runs over the in-memory world (AGENTS.md §45 — an ALLOW is evidence
only when a DENY also holds; there is no cross-tenant/allowed-op leak).
"""
from __future__ import annotations

import asyncio

from tests.unit.api.fakes import consultant_user, member_user, staff_user

ORG_A = "org-a"
FIRM_ID = "firm-1"
CONSULTANT_ID = "u-cons"
CLIENT_A = "client-a"

REL_DECISION = "/api/v3/consultants/me/relationship-requests/{rid}/decision"
MODE_ADMIN = "/api/v3/admin/consultants/mode-change-requests"
MODE_ADMIN_DECISION = "/api/v3/admin/consultants/mode-change-requests/{rid}/decision"


def _seed_firm(world, *, can_manage_clients: bool = True):
    world.consultants.seed_profile(FIRM_ID, CONSULTANT_ID, "Acme Consultants")
    world.consultants.seed_firm_member(
        FIRM_ID,
        CONSULTANT_ID,
        role="owner",
        can_view_client=True,
        can_manage_clients=can_manage_clients,
    )
    return consultant_user(CONSULTANT_ID, "cons@example.test")


def _make_rel_request(
    world, *, firm_id: str = FIRM_ID, org_id: str = ORG_A, rtype: str = "end_relationship"
):
    return asyncio.run(
        world.consultants.create_relationship_request(
            organization_id=org_id,
            consultant_id=firm_id,
            request_type=rtype,
            initiated_by=None,
            initiated_capacity="client",
            reason="Please review",
        )
    )


def _seed_mode_request(
    world, *, firm_id: str = FIRM_ID, requested_mode: str = "white_label"
):
    return asyncio.run(
        world.consultants.create_mode_change_request(
            firm_id=firm_id,
            requested_by=CONSULTANT_ID,
            current_mode="standard",
            requested_mode=requested_mode,
            reason="Upgrade",
        )
    )


# ---------------------------------------------------------------------------
# PD-5 — firm-side relationship-request decision + non-destructive termination
# ---------------------------------------------------------------------------
class TestRelationshipRequestDecision:
    def test_approve_end_relationship_ends_non_destructively(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        record = _make_rel_request(world)
        resp = client.post(
            REL_DECISION.format(rid=record["id"]),
            json={"decision": "approve", "confirmed": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["request"]["status"] == "completed"
        assert body["ended_client_id"] == CLIENT_A
        # Non-destructive: the relationship ROW still exists, merely ended.
        row = asyncio.run(world.consultants.get_client(CLIENT_A))
        assert row is not None and row.status == "ended"

    def test_approve_end_relationship_requires_confirmation(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        record = _make_rel_request(world)
        resp = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "approve"}
        )
        assert resp.status_code == 428
        # The relationship was NOT ended by an unconfirmed request.
        row = asyncio.run(world.consultants.get_client(CLIENT_A))
        assert row.status == "active"

    def test_reject_keeps_relationship_active(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        record = _make_rel_request(world)
        resp = client.post(
            REL_DECISION.format(rid=record["id"]),
            json={"decision": "reject", "decision_note": "Not now"},
        )
        assert resp.status_code == 200
        assert resp.json()["request"]["status"] == "cancelled"
        assert asyncio.run(world.consultants.get_client(CLIENT_A)).status == "active"

    def test_approve_change_consultant_confirms_without_state_change(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        record = _make_rel_request(world, rtype="change_consultant")
        resp = client.post(
            REL_DECISION.format(rid=record["id"]),
            json={"decision": "approve", "confirmed": True},
        )
        assert resp.status_code == 200
        assert resp.json()["request"]["status"] == "confirmed"
        assert asyncio.run(world.consultants.get_client(CLIENT_A)).status == "active"

    def test_decision_of_another_firms_request_is_404(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        record = _make_rel_request(world, firm_id="firm-2", org_id="org-foreign")
        resp = client.post(
            REL_DECISION.format(rid=record["id"]),
            json={"decision": "approve", "confirmed": True},
        )
        assert resp.status_code == 404

    def test_second_decision_is_409(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        record = _make_rel_request(world)
        first = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert first.status_code == 200
        second = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert second.status_code == 409

    def test_unknown_request_is_404(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        resp = client.post(
            REL_DECISION.format(rid="does-not-exist"), json={"decision": "reject"}
        )
        assert resp.status_code == 404

    def test_non_consultant_cannot_decide(self, world, client, user_provider):
        user_provider.set_user(member_user(ORG_A, "u-client", "c@client.test"))
        record = _make_rel_request(world)
        resp = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert resp.status_code == 403

    def test_requires_manage_clients_capability(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world, can_manage_clients=False))
        record = _make_rel_request(world)
        resp = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert resp.status_code == 403

    def test_lost_atomic_race_is_409_not_null_body(
        self, world, client, user_provider
    ):
        # The read pre-check sees 'requested', but a concurrent decision wins the
        # atomic claim (decide_* returns None). The route must surface a 409
        # conflict, never a 200 with a null request body.
        user_provider.set_user(_seed_firm(world))
        record = _make_rel_request(world)

        async def _lost_race(*args, **kwargs):
            return None

        world.consultants.decide_relationship_request = _lost_race
        resp = client.post(
            REL_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# PO-1 — CarbonTally Admin mode-change decision (the ONLY commercial_mode writer)
# ---------------------------------------------------------------------------
class TestModeChangeDecision:
    def _admin(self, user_provider):
        user_provider.set_user(staff_user(user_id="u-admin", role_name="admin"))

    def test_admin_lists_pending_mode_requests(self, world, client, user_provider):
        self._admin(user_provider)
        _seed_mode_request(world)
        resp = client.get(MODE_ADMIN)
        assert resp.status_code == 200
        assert [r["requested_mode"] for r in resp.json()["requests"]] == ["white_label"]

    def test_admin_approves_with_apply_now(self, world, client, user_provider):
        self._admin(user_provider)
        world.consultants.seed_branding(FIRM_ID, brand_name="Acme", commercial_mode="standard")
        record = _seed_mode_request(world)
        resp = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]),
            json={"decision": "approve", "apply_now": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["request"]["status"] == "approved"
        assert body["applied_mode"] == "white_label"
        assert world.consultants._brandings[FIRM_ID].commercial_mode == "white_label"

    def test_admin_approves_deferred_without_apply(self, world, client, user_provider):
        self._admin(user_provider)
        world.consultants.seed_branding(FIRM_ID, brand_name="Acme", commercial_mode="standard")
        record = _seed_mode_request(world)
        resp = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]), json={"decision": "approve"}
        )
        assert resp.status_code == 200
        assert resp.json()["applied_mode"] is None
        # Deferred: the firm's mode is NOT changed until the boundary.
        assert world.consultants._brandings[FIRM_ID].commercial_mode == "standard"

    def test_admin_rejects(self, world, client, user_provider):
        self._admin(user_provider)
        record = _seed_mode_request(world)
        resp = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]),
            json={"decision": "reject", "decision_note": "Not entitled"},
        )
        assert resp.status_code == 200
        assert resp.json()["request"]["status"] == "rejected"

    def test_admin_second_decision_is_409(self, world, client, user_provider):
        self._admin(user_provider)
        record = _seed_mode_request(world)
        first = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert first.status_code == 200
        second = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert second.status_code == 409

    def test_unknown_mode_request_is_404(self, world, client, user_provider):
        self._admin(user_provider)
        resp = client.post(
            MODE_ADMIN_DECISION.format(rid="nope"), json={"decision": "reject"}
        )
        assert resp.status_code == 404

    def test_consultant_cannot_use_admin_surface(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        record = _seed_mode_request(world)
        assert client.get(MODE_ADMIN).status_code == 403
        assert (
            client.post(
                MODE_ADMIN_DECISION.format(rid=record["id"]),
                json={"decision": "approve", "apply_now": True},
            ).status_code
            == 403
        )

    def test_lost_atomic_race_is_409_not_null_body(
        self, world, client, user_provider
    ):
        # Same concurrent-decision race as the PD-5 surface: a lost atomic claim
        # must be a 409 conflict, never a 200 with a null request body.
        self._admin(user_provider)
        record = _seed_mode_request(world)

        async def _lost_race(*args, **kwargs):
            return None

        world.consultants.decide_mode_change_request = _lost_race
        resp = client.post(
            MODE_ADMIN_DECISION.format(rid=record["id"]), json={"decision": "reject"}
        )
        assert resp.status_code == 409


