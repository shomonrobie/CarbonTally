"""D19 consultant-client lifecycle tests (D27 / D19 §4, §10).

Covers the ACTIVE / SUSPENDED / ENDED lifecycle vocabulary, the transition
guards and the access-termination semantics enforced by the API surface.
"""
from __future__ import annotations

from tests.unit.api.fakes import consultant_user


def _seed_consultant(world, *, user_id="consultant-1", firm_id="firm-1"):
    world.consultants.seed_profile(firm_id, user_id, "Net Zero Advisory")
    world.consultants.seed_firm_member(
        firm_id, user_id, role="owner",
        can_manage_clients=True, can_manage_team=True,
    )


class TestLifecycleDomain:
    def test_transition_table(self) -> None:
        from domain.partners import can_transition_client_lifecycle

        assert can_transition_client_lifecycle("active", "suspended")
        assert can_transition_client_lifecycle("active", "ended")
        assert can_transition_client_lifecycle("suspended", "active")
        assert can_transition_client_lifecycle("suspended", "ended")
        assert can_transition_client_lifecycle("ended", "active")
        # Unknown/legacy NULL statuses behave like active (pre-D19 default).
        assert can_transition_client_lifecycle(None, "suspended")

    def test_invalid_transition_denied(self) -> None:
        from domain.partners import can_transition_client_lifecycle

        assert not can_transition_client_lifecycle("active", "not-a-status")
        assert not can_transition_client_lifecycle("ended", "suspended")


class TestLifecycleApi:
    def test_suspend_client(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="active")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/suspend")
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"

    def test_end_client(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="active")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ended"
        assert resp.json()["ended_by"] == "consultant-1"

    def test_reactivate_client(self, world, client, user_provider) -> None:
        _seed_consultant(world)
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="ended")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/reactivate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_lifecycle_transition_requires_manage_clients(self, world, client, user_provider) -> None:
        world.consultants.seed_profile("firm-1", "consultant-1", "Net Zero Advisory")
        world.consultants.seed_firm_member("firm-1", "consultant-1", role="consultant")
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="active")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post("/api/v3/consultants/clients/client-1/end")
        assert resp.status_code == 403

    def test_ended_grant_loses_client_access(self, world, client, user_provider) -> None:
        """A consultant with an ENDED grant cannot read the client workspace."""
        _seed_consultant(world)
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="ended")
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.get("/api/v3/consultants/clients/client-1/reports")
        assert resp.status_code == 403
