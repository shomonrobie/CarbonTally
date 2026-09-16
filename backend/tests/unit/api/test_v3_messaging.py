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


class TestMessagingServerAuthoritativeParticipantWrites:
    """P8-FIN-02 / D-7 — participant creation is SERVER-AUTHORITATIVE.

    The browser never inserts ``conversation_participants`` rows: the API adds the
    creator and (on request) one authorised CarbonTally support participant that
    the server resolves from the staff table.
    """

    @staticmethod
    def _seed_support(world, user_id: str = "u-support") -> None:
        import asyncio

        from domain.staff import StaffProfile, StaffRole

        world.staff.seed_role(
            StaffRole(id="role-admin", name="admin", permissions={"can_manage_staff": True})
        )
        asyncio.run(
            world.staff.save(
                StaffProfile(
                    id="sp-support",
                    user_id=user_id,
                    first_name="Support",
                    last_name="One",
                    email="support@carbontally.test",
                    role_id="role-admin",
                    entity_id=None,
                )
            )
        )

    def test_org_user_creates_support_conversation_with_server_resolved_counterparty(
        self, world, client, user_provider
    ) -> None:
        import asyncio

        self._seed_support(world)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.post(
            "/api/v3/messaging/conversations",
            json={
                "organization_id": "org-a",
                "subject": "Need help with my upload",
                "counterparty": "support",
            },
        )

        assert resp.status_code == 201
        body = resp.json()["conversation"]
        assert body["counterparty_user_id"] == "u-support"
        assert body["organization_id"] == "org-a"

        participants = asyncio.run(world.messaging.list_participants(body["id"]))
        assert {p.user_id for p in participants} == {"member-1", "u-support"}

        actions = [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)
        assert "msg:conversation_created" in actions

    def test_support_counterparty_requires_an_authorised_participant(
        self, client, user_provider
    ) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={
                "organization_id": "org-a",
                "subject": "Support?",
                "counterparty": "support",
            },
        )
        assert resp.status_code == 409

    def test_unknown_counterparty_value_is_rejected(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "x", "counterparty": "ceo"},
        )
        assert resp.status_code == 422

    def test_default_conversation_keeps_creator_only_participants(
        self, world, client, user_provider
    ) -> None:
        import asyncio

        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "Consultant thread"},
        )
        assert resp.status_code == 201
        body = resp.json()["conversation"]
        assert body["counterparty_user_id"] is None
        participants = asyncio.run(world.messaging.list_participants(body["id"]))
        assert [p.user_id for p in participants] == ["member-1"]

    def test_entity_staff_cannot_request_a_support_counterparty(
        self, client, user_provider
    ) -> None:
        from tests.unit.api.fakes import entity_operator_user

        user_provider.set_user(entity_operator_user("pe-1"))
        resp = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "x", "counterparty": "support"},
        )
        assert resp.status_code == 403

    def test_foreign_org_member_cannot_create_or_reach_another_tenant(
        self, world, client, user_provider
    ) -> None:
        import asyncio

        user_provider.set_user(member_user("org-b", "member-b", "b@test"))
        create = client.post(
            "/api/v3/messaging/conversations",
            json={"organization_id": "org-a", "subject": "cross tenant"},
        )
        assert create.status_code == 403

        conversation = asyncio.run(
            world.messaging.create_conversation(
                organization_id="org-a", subject="Thread", created_by="member-1"
            )
        )
        assert client.get(
            f"/api/v3/messaging/conversations/{conversation.id}/messages"
        ).status_code == 403
        assert client.post(
            f"/api/v3/messaging/conversations/{conversation.id}/messages",
            json={"content": "intrusion"},
        ).status_code == 403

    def test_message_carries_conversation_organization_scope_and_is_audited(
        self, world, client, user_provider
    ) -> None:
        import asyncio

        conversation = asyncio.run(
            world.messaging.create_conversation(
                organization_id="org-a", subject="Thread", created_by="member-1"
            )
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            f"/api/v3/messaging/conversations/{conversation.id}/messages",
            json={"content": "hello"},
        )
        assert resp.status_code == 201

        messages = asyncio.run(world.messaging.list_messages(conversation.id))
        assert [m.organization_id for m in messages] == ["org-a"]

        actions = [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)
        assert "msg:message_sent" in actions

    def test_consultant_with_ended_grant_cannot_send_into_conversation(
        self, world, client, user_provider
    ) -> None:
        import asyncio

        world.consultants.seed_profile("firm-1", "consultant-1", "Net Zero Advisory")
        world.consultants.seed_firm_member(
            "firm-1", "consultant-1", role="owner", can_manage_clients=True
        )
        world.consultants.seed_client("client-1", "firm-1", "org-a", "Org A", status="ended")
        conversation = asyncio.run(
            world.messaging.create_conversation(
                organization_id="org-a", subject="Thread", created_by="member-1"
            )
        )
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.post(
            f"/api/v3/messaging/conversations/{conversation.id}/messages",
            json={"content": "should be denied"},
        )
        assert resp.status_code == 403


class TestLegacyBrowserChatWritePathIsRetired:
    """P8-FIN-02 / D-7 — the browser-side participant/message write path is gone.

    Guards the *source* (not just a rendered path): the legacy widget must not
    write ``conversations`` / ``conversation_participants`` / ``messages``
    directly, must not write the nonexistent ``conversations.is_group`` column,
    and the server repository must never reference it either.
    """

    @staticmethod
    def _repo_root():
        from pathlib import Path

        return Path(__file__).resolve().parents[4]

    def test_server_messaging_repository_never_writes_is_group(self) -> None:
        root = self._repo_root()
        for relative in ("backend/data/messaging.py", "backend/api/v3_messaging.py"):
            source = (root / relative).read_text(encoding="utf-8")
            assert "is_group" not in source, f"{relative} references is_group"

    def test_chat_components_do_not_write_conversations_or_participants(self) -> None:
        import re

        root = self._repo_root()
        chat = root / "frontend" / "src" / "components" / "chat"
        # Direct browser WRITES to the messaging tables are retired; chained
        # READS/UPDATEs (RLS-permitted) are out of scope for this guard.
        write = re.compile(
            r"\.from\('(conversations|conversation_participants|messages)'\)\s*"
            r"\.(insert|upsert|delete)\("
        )
        offenders: list[str] = []
        for path in sorted(chat.glob("*.jsx")):
            source = path.read_text(encoding="utf-8")
            if write.search(source):
                offenders.append(path.name)
            assert "is_group" not in source, f"{path.name} references is_group"
        assert offenders == [], f"browser-side messaging writes remain: {offenders}"

    def test_chat_components_do_not_peer_read_users(self) -> None:
        root = self._repo_root()
        chat = root / "frontend" / "src" / "components" / "chat"
        offenders = [
            path.name
            for path in sorted(chat.glob("*.jsx"))
            if ".from('users')" in path.read_text(encoding="utf-8")
        ]
        assert offenders == [], f"direct users peer reads remain: {offenders}"
