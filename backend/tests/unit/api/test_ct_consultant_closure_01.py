"""CT-CONSULTANT-PLATFORM-CLOSURE-01 — safely-implementable closure increments.

Binding source: ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md``
(authority) plus ``CT-CONSULTANT-DECISION-STATE-ARTEFACT-AUDIT-01`` and the
independent ``CT-CONSULTANT-UX-PARITY-INDEPENDENT-VERIFY-01``.

Covered here (all server-side, over the in-memory world; AGENTS.md §45 — an
ALLOW is evidence only when it returns the authorised tenant's own data and a
DENY never leaks it):

* §10  firm-task ``client_id`` is validated SERVER-SIDE (F-IND-1 / PD-3A): a
       foreign / inactive / nonexistent id is rejected with ONE uniform response
       (no access oracle); a firm-wide task is unaffected.
* §7   firm-scoped READ surfaces for relationship change/end requests and
       mode-change requests (the decision consumer itself is gated by PD-5).
* §6.1 (PO-2) consultant-side VIEW of a managed client's users, admission-checked.

Deliberately NOT covered (open Product-Owner decisions — fail closed, not
invented): the relationship/mode request APPROVE/REJECT authority (PD-5),
client-user invite/manage/revoke (PD-1A, PD-2A).
"""
from __future__ import annotations

import asyncio

import auth
import pytest

from tests.unit.api.fakes import consultant_user, member_user

ORG_A = "org-a"
FIRM_ID = "firm-1"
CONSULTANT_ID = "u-cons"
CLIENT_A = "client-a"

TASKS_PATH = "/api/v3/consultants/me/tasks"
REL_REQ_PATH = "/api/v3/consultants/me/relationship-requests"
MODE_REQ_PATH = "/api/v3/consultants/me/mode-change-requests"
CLIENT_USERS_PATH = "/api/v3/consultants/clients/{client_id}/users"


@pytest.fixture
def live_tenants(monkeypatch):
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_firm(world, *, can_manage_team: bool = True):
    """Seed a firm with one owner member (firm administration capable)."""
    world.consultants.seed_profile(FIRM_ID, CONSULTANT_ID, "Acme Consultants")
    world.consultants.seed_firm_member(
        FIRM_ID,
        CONSULTANT_ID,
        role="owner",
        can_view_client=True,
        can_manage_clients=True,
        can_manage_team=can_manage_team,
    )
    return consultant_user(CONSULTANT_ID, "cons@example.test")


# ---------------------------------------------------------------------------
# §10 — firm-task client_id server-side validation (F-IND-1 / PD-3A)
# ---------------------------------------------------------------------------
class TestFirmTaskClientLinkValidation:
    def _post(self, client, **payload):
        body = {"task_title": "Chase missing DEC data"}
        body.update(payload)
        return client.post(TASKS_PATH, json=body)

    def test_firm_wide_task_without_client_is_allowed(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        resp = self._post(client)
        assert resp.status_code == 201
        assert resp.json()["client_id"] is None

    def test_task_linking_own_active_client_row_is_allowed(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        resp = self._post(client, client_id=CLIENT_A)
        assert resp.status_code == 201
        assert resp.json()["client_id"] == CLIENT_A

    def test_task_linking_own_client_org_id_is_allowed(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        assert self._post(client, client_id=ORG_A).status_code == 201

    def test_task_linking_foreign_client_is_rejected(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        world.consultants.seed_client("client-f", "firm-2", "org-foreign", "Rival Co")
        assert self._post(client, client_id="client-f").status_code == 422

    def test_task_linking_nonexistent_client_is_rejected(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        assert self._post(client, client_id="does-not-exist").status_code == 422

    def test_task_linking_inactive_client_is_rejected(
        self, world, client, user_provider
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(
            "client-susp", FIRM_ID, "org-susp", "Suspended Ltd", status="suspended"
        )
        assert self._post(client, client_id="client-susp").status_code == 422

    def test_foreign_and_nonexistent_are_indistinguishable(
        self, world, client, user_provider
    ):
        """No access oracle: the denial never reveals whether the id exists."""
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        world.consultants.seed_client("client-f", "firm-2", "org-foreign", "Rival Co")
        foreign = self._post(client, client_id="client-f")
        absent = self._post(client, client_id="no-such-id")
        assert foreign.status_code == absent.status_code == 422
        # The error envelope is identical apart from per-request volatile fields:
        # the caller cannot tell "not mine" from "does not exist".
        volatile = ("timestamp", "request_id", "path")
        f_err = {k: v for k, v in foreign.json()["error"].items() if k not in volatile}
        a_err = {k: v for k, v in absent.json()["error"].items() if k not in volatile}
        assert f_err == a_err
        assert f_err["code"]  # a stable error code, identical for both — no oracle

    def test_non_consultant_cannot_create_a_task(self, world, client, user_provider):
        user_provider.set_user(member_user(ORG_A, "u-client", "c@client.test"))
        assert self._post(client).status_code == 403


# ---------------------------------------------------------------------------
# §7 — request REVIEW surfaces (read-only; the decision consumer is PD-5)
# ---------------------------------------------------------------------------
class TestRequestReviewSurfaces:
    def test_firm_lists_its_relationship_requests(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        asyncio.run(
            world.consultants.create_relationship_request(
                organization_id=ORG_A,
                consultant_id=FIRM_ID,
                request_type="end_relationship",
                initiated_by=None,
                initiated_capacity="client",
                reason="switching advisers",
            )
        )
        resp = client.get(REL_REQ_PATH)
        assert resp.status_code == 200
        requests = resp.json()["requests"]
        assert len(requests) == 1
        assert requests[0]["request_type"] == "end_relationship"
        assert requests[0]["status"] == "requested"

    def test_relationship_requests_are_firm_scoped(self, world, client, user_provider):
        """Cross-firm isolation: another firm's request is never returned."""
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        asyncio.run(
            world.consultants.create_relationship_request(
                organization_id="org-foreign",
                consultant_id="firm-2",
                request_type="change_consultant",
                initiated_by=None,
                initiated_capacity="client",
            )
        )
        resp = client.get(REL_REQ_PATH)
        assert resp.status_code == 200
        assert resp.json()["requests"] == []

    def test_firm_lists_its_mode_change_requests(self, world, client, user_provider):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_branding(
            FIRM_ID, brand_name="Acme Green", commercial_mode="co_branded"
        )
        created = client.post(MODE_REQ_PATH, json={"requested_mode": "white_label"})
        assert created.status_code == 201
        resp = client.get(MODE_REQ_PATH)
        assert resp.status_code == 200
        requests = resp.json()["requests"]
        assert len(requests) == 1
        assert requests[0]["requested_mode"] == "white_label"
        assert requests[0]["status"] == "requested"

    def test_non_consultant_cannot_list_requests(self, world, client, user_provider):
        user_provider.set_user(member_user(ORG_A, "u-client", "c@client.test"))
        assert client.get(REL_REQ_PATH).status_code == 403
        assert client.get(MODE_REQ_PATH).status_code == 403


# ---------------------------------------------------------------------------
# §6.1 (PO-2) — consultant-side VIEW of a managed client's users
# ---------------------------------------------------------------------------
class TestConsultantViewsClientUsers:
    def test_consultant_views_client_users_of_an_active_client(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(CLIENT_A, FIRM_ID, ORG_A, "ACME LTD")
        world.organizations.add_member_record(
            {
                "id": "m-1",
                "organization_id": ORG_A,
                "user_id": "cu-1",
                "role": "owner",
                "is_active": True,
                "email": "owner@client.test",
            }
        )
        resp = client.get(CLIENT_USERS_PATH.format(client_id=CLIENT_A))
        assert resp.status_code == 200
        body = resp.json()
        assert body["organization_id"] == ORG_A
        assert [u["user_id"] for u in body["users"]] == ["cu-1"]

    def test_client_users_require_an_active_relationship(
        self, world, client, user_provider, live_tenants
    ):
        """D15 — a non-active grant serves the consultant nothing."""
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_client(
            CLIENT_A, FIRM_ID, ORG_A, "ACME LTD", status="ended"
        )
        assert (
            client.get(CLIENT_USERS_PATH.format(client_id=CLIENT_A)).status_code == 403
        )

    def test_client_users_denied_for_another_firms_client(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_firm(world))
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        world.consultants.seed_client("client-f", "firm-2", "org-foreign", "Rival Co")
        assert (
            client.get(CLIENT_USERS_PATH.format(client_id="client-f")).status_code
            == 403
        )



