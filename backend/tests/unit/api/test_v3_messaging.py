"""API contract tests for the V3 consultant-client messaging (D27 / D19 §16).

Verifies: org members and active-grant consultants may create/list/send in
conversations; Processing Entity staff and non-granted callers are denied.
"""
from __future__ import annotations

from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_admin_user,
)


class TestMessaging:
    def test_org_member_creates_conversation(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Documentation request"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["conversation"]["organization_id"] == "org-a"

    def test_consultant_with_active_grant_creates_conversation(
        self, world, client, user_provider
    ) -> None:
        world.consultants.seed_profile("firm-1", "consultant-1", "Net Zero Advisory")
        world.consultants.seed_firm_member(
            "firm-1", "consultant-1", role="owner",
            can_manage_clients=True, can_manage_team=True,
        )
        world.consultants.seed_client(
            "client-1", "firm-1", "org-a", "Org A", status="active"
        )
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "From the consultant"},
        )
        assert resp.status_code == 201

    def test_consultant_with_ended_grant_denied(self, world, client, user_provider) -> None:
        world.consultants.seed_profile("firm-1", "consultant-1", "Net Zero Advisory")
        world.consultants.seed_firm_member(
            "firm-1", "consultant-1", role="owner",
            can_manage_clients=True, can_manage_team=True,
        )
        world.consultants.seed_client(
            "client-1", "firm-1", "org-a", "Org A", status="ended"
        )
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Should be denied"},
        )
        assert resp.status_code == 403

    def test_entity_staff_never_messages(self, client, user_provider) -> None:
        from tests.unit.api.fakes import entity_operator_user

        user_provider.set_user(entity_operator_user("pe-1"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Entity attempt"},
        )
        assert resp.status_code == 403


    def test_staff_admin_can_message_org_n1(self, world, client, user_provider) -> None:
        """N1 — CarbonTally support/admin (internal staff, can_manage_staff) may
        message an authorised organisation."""
        import asyncio

        from domain.staff import StaffProfile, StaffRole

        world.staff.seed_role(
            StaffRole(id="role-admin", name="admin", permissions={"can_manage_staff": True})
        )
        asyncio.run(
            world.staff.save(
                StaffProfile(
                    id="sp-support",
                    user_id="u-support",
                    first_name="Support",
                    last_name="One",
                    email="support@carbontally.test",
                    role_id="role-admin",
                    entity_id=None,
                )
            )
        )
        from tests.unit.api.fakes import staff_user

        user_provider.set_user(staff_user("u-support", email="support@carbontally.test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Support thread"},
        )
        assert resp.status_code == 201

    def test_general_staff_cannot_message_n1(self, world, client, user_provider) -> None:
        """N1 — general CarbonTally employees do NOT automatically receive
        messaging access (no can_manage_staff permission)."""
        import asyncio

        from domain.staff import StaffProfile, StaffRole

        world.staff.seed_role(
            StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
        )
        asyncio.run(
            world.staff.save(
                StaffProfile(
                    id="sp-op",
                    user_id="u-op",
                    first_name="Op",
                    last_name="One",
                    email="op@carbontally.test",
                    role_id="role-operator",
                    entity_id=None,
                )
            )
        )
        from tests.unit.api.fakes import staff_user

        user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Operator attempt"},
        )
        assert resp.status_code == 403

    def test_send_and_list_messages(self, world, client, user_provider) -> None:
        import asyncio

        conversation = asyncio.run(
            world.messaging.create_conversation(
                organization_id="org-a", subject="Thread", created_by="member-1"
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            f"/api/v3/messaging/conversations/{conversation.id}/messages",
            json={"content": "Hello from the customer"},
        )
        assert resp.status_code == 201
        resp2 = client.get(
            f"/api/v3/messaging/conversations/{conversation.id}/messages"
        )
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 1

    def test_foreign_user_cannot_read_conversation(self, world, client, user_provider) -> None:
        import asyncio

        conversation = asyncio.run(
            world.messaging.create_conversation(
                organization_id="org-a", subject="Thread", created_by="member-1"
            )
        )
        user_provider.set_user(member_user("org-b", "member-2", "m2@test"))
        resp = client.get(
            f"/api/v3/messaging/conversations/{conversation.id}/messages"
        )
        assert resp.status_code == 403
