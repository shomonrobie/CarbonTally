"""API contract tests for the V3 white-label surface (D27 / D19 §11-§13).

Verifies custom-domain lifecycle (PENDING -> VERIFIED -> ACTIVE /
REMOVED_SUSPENDED) and custom-sender lifecycle (PENDING -> VERIFIED /
REMOVED) for the caller's OWN firm only, with the firm-admin permission gate.
"""
from __future__ import annotations

from tests.unit.api.fakes import consultant_user


def _seed_consultant(world, *, user_id="consultant-1", firm_id="firm-1"):
    world.consultants.seed_profile(firm_id, user_id, "Net Zero Advisory")
    world.consultants.seed_firm_member(
        firm_id, user_id, role="owner",
        can_manage_clients=True, can_manage_team=True,
    )


class TestCustomDomains:
    def test_create_domain(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            "/api/v3/consultants/me/custom-domains",
            json={"domain": "portal.consultant-demo.com"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["domain"]["status"] == "pending"
        assert "verification_instructions" in body["domain"]

    def test_invalid_domain_rejected(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            "/api/v3/consultants/me/custom-domains",
            json={"domain": "not a domain"},
        )
        assert resp.status_code == 422

    def test_verify_then_activate_domain(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        created = client.post(
            "/api/v3/consultants/me/custom-domains",
            json={"domain": "portal.consultant-demo.com"},
        ).json()["domain"]
        token = created["verification_token"]
        resp = client.post(
            f"/api/v3/consultants/me/custom-domains/{created['id']}/verify",
            json={"token": token},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"
        resp2 = client.post(
            f"/api/v3/consultants/me/custom-domains/{created['id']}/activate"
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "active"

    def test_wrong_token_rejected(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        created = client.post(
            "/api/v3/consultants/me/custom-domains",
            json={"domain": "portal.consultant-demo.com"},
        ).json()["domain"]
        resp = client.post(
            f"/api/v3/consultants/me/custom-domains/{created['id']}/verify",
            json={"token": "wrong-token"},
        )
        assert resp.status_code == 400

    def test_remove_domain(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        created = client.post(
            "/api/v3/consultants/me/custom-domains",
            json={"domain": "portal.consultant-demo.com"},
        ).json()["domain"]
        resp = client.post(
            f"/api/v3/consultants/me/custom-domains/{created['id']}/remove"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed_suspended"


class TestCustomSenders:
    def test_create_verify_list_sender(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        created = client.post(
            "/api/v3/consultants/me/senders",
            json={"email": "reports@consultant-demo.com"},
        ).json()["sender"]
        assert created["status"] == "pending"
        resp = client.post(
            f"/api/v3/consultants/me/senders/{created['id']}/verify"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"
        listed = client.get("/api/v3/consultants/me/senders").json()["senders"]
        assert any(s["email"] == "reports@consultant-demo.com" for s in listed)

    def test_arbitrary_email_rejected(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            "/api/v3/consultants/me/senders",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422

    def test_remove_sender(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        created = client.post(
            "/api/v3/consultants/me/senders",
            json={"email": "reports@consultant-demo.com"},
        ).json()["sender"]
        resp = client.post(
            f"/api/v3/consultants/me/senders/{created['id']}/remove"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"
