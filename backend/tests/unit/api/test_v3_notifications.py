"""API contract tests for the V3 Notifications surface (D25 + D26 pagination)."""

from __future__ import annotations

from tests.unit.api.fakes import member_user


class TestV3Notifications:
    def test_list_notifications_bounded_defaults(
        self, client, user_provider
    ) -> None:
        """Per-user notifications list is bounded with stable defaults (D26
        scale hardening — never an unbounded per-user list)."""
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get("/api/v3/notifications")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "notifications": [],
            "total": 0,
            "limit": 100,
            "offset": 0,
        }

    def test_list_notifications_limit_clamped(self, client, user_provider) -> None:
        """Out-of-range limit/offset are clamped to the safe window (1..500)."""
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get("/api/v3/notifications", params={"limit": 9999})
        assert resp.status_code == 200
        assert resp.json()["limit"] == 500

        resp = client.get("/api/v3/notifications", params={"limit": -5, "offset": -3})
        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 1
        assert body["offset"] == 0

    def test_list_notifications_requires_auth(self, client, user_provider) -> None:
        user_provider.set_unauthenticated()
        resp = client.get("/api/v3/notifications")
        assert resp.status_code == 401

    def test_mark_read_requires_auth(self, client, user_provider) -> None:
        user_provider.set_unauthenticated()
        resp = client.post("/api/v3/notifications/00000000-0000-4000-8000-000000000000/read")
        assert resp.status_code == 401
