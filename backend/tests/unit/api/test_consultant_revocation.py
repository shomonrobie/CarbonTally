"""WS6 / SEC-0003 — consultant-client revocation role-model tests.

Approved product decision:
    Consultant Owner/Admin/Manager may revoke a consultant-client
    relationship; Consultant Member/Viewer may not.

Revocation must:
  * soft-revoke the active grant (status -> 'ended') — NOT account deletion,
  * preserve client data / documents / emissions / calculation history /
    evidence (the relationship row and the organisation are retained),
  * remain auditable (ended_by + audit event),
  * stop granting consultant access (D15: access requires status='active').

The role gate is role-based (owner/admin/manager), deliberately independent of
the ``can_manage_clients`` capability flag for this specific action.
"""
from __future__ import annotations

import pytest

from tests.unit.api.fakes import consultant_user

ALLOWED_ROLES = ("owner", "admin", "manager")
DENIED_ROLES = ("consultant", "viewer")  # member ('consultant') and viewer


def _seed_consultant(world, *, user_id="consultant-1", firm_id="firm-1",
                     role="owner", can_manage_clients=True):
    world.consultants.seed_profile(firm_id, user_id, "Net Zero Advisory")
    world.consultants.seed_firm_member(
        firm_id, user_id, role=role, can_manage_clients=can_manage_clients,
    )


def _seed_active_client(world, client_id="client-1"):
    world.consultants.seed_client(client_id, "firm-1", "org-a", "Org A", status="active")


class TestRevocationRoleAuthority:
    @pytest.mark.parametrize("role", ALLOWED_ROLES)
    def test_owner_admin_manager_may_end_relationship(self, world, client, user_provider, role):
        _seed_consultant(world, role=role, can_manage_clients=False)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "ended"

    @pytest.mark.parametrize("role", DENIED_ROLES)
    def test_member_viewer_may_not_end_relationship(self, world, client, user_provider, role):
        # Even with can_manage_clients=true, a Member/Viewer must be denied
        # (the decision is role-based for revocation).
        _seed_consultant(world, role=role, can_manage_clients=True)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 403, resp.text

    @pytest.mark.parametrize("role", DENIED_ROLES)
    def test_member_viewer_may_not_suspend(self, world, client, user_provider, role):
        _seed_consultant(world, role=role, can_manage_clients=True)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/suspend")
        assert resp.status_code == 403, resp.text

    @pytest.mark.parametrize("role", DENIED_ROLES)
    def test_member_viewer_may_not_reactivate(self, world, client, user_provider, role):
        _seed_consultant(world, role=role, can_manage_clients=True)
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="ended")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/reactivate")
        assert resp.status_code == 403, resp.text


class TestRevocationPreservesProvenance:
    def test_end_keeps_relationship_row_and_organisation(self, world, client, user_provider):
        """Revocation soft-revokes the grant; it is NOT client/account deletion."""
        _seed_consultant(world)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ended"
        assert resp.json().get("ended_by") == "consultant-1"

        # The relationship row still exists (ownership-only read) and the
        # organisation still resolves — client data is preserved.
        detail = client.get("/api/v3/consultants/clients/client-1")
        assert detail.status_code == 200
        assert detail.json()["client"]["status"] == "ended"
        assert detail.json()["client"]["organization_id"] == "org-a"
        assert detail.json()["organization_name"] == "Org A"

    def test_end_records_audit_event(self, world, client, user_provider):
        _seed_consultant(world)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        client.post("/api/v3/consultants/clients/client-1/end")
        actions = [e.action for e in world.audit._entries]
        assert "consultant_client.ended" in actions, actions

    def test_revoked_relationship_no_longer_grants_access(self, world, client, user_provider):
        """D15 — after revocation the consultant cannot read the client workspace."""
        _seed_consultant(world)
        _seed_active_client(world)
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 200
        data_resp = client.get("/api/v3/consultants/clients/client-1/reports")
        assert data_resp.status_code == 403
