"""API contract tests for the V3 Issue surface (ADR-V3-009)."""

from __future__ import annotations

import asyncio

from tests.unit.api.fakes import (
    InMemoryWorld,
    Issue,
    ProcessingEntity,
    member_user,
)


def _await(coro) -> None:
    asyncio.run(coro)


def _seed_issue(*, issue_id: str = "issue-1", org_id: str = "org-a") -> Issue:
    return Issue(
        id=issue_id,
        title="Missing invoice page",
        organization_id=org_id,
        status="open",
    )


class TestV3Issues:
    def test_create_issue(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.post(
            "/api/v3/issues",
            json={
                "title": "Missing invoice page",
                "organization_id": "org-a",
                "severity": "high",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "open"
        assert body["entity_id"] is None

    def test_list_issues_excludes_entity_scoped(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        _await(world.issues.save(_seed_issue()))
        _await(world.issues.save(
            Issue(
                id="issue-entity",
                title="Entity issue",
                organization_id="org-a",
                entity_id="pe-1",
                status="open",
            )
        ))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get("/api/v3/issues", params={"organization_id": "org-a"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["issues"][0]["id"] == "issue-1"

    def test_list_issues_paginated_bounds_and_total(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        """D26 scale hardening — customer issue list is bounded with an
        accurate full ``total`` (stable ordering ``created_at DESC, id``)."""
        for i in range(5):
            _await(world.issues.save(_seed_issue(issue_id=f"issue-{i}")))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        # Page 1: 2 rows, total reflects the full org count.
        resp = client.get(
            "/api/v3/issues",
            params={"organization_id": "org-a", "limit": 2, "offset": 0},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["issues"]) == 2

        # Page 3: offset past the end -> empty page, total unchanged.
        resp = client.get(
            "/api/v3/issues",
            params={"organization_id": "org-a", "limit": 2, "offset": 4},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["issues"]) == 1

    def test_list_issues_pagination_params_validated(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        """Out-of-range limit/offset are rejected by the API (1..500 / >=0)."""
        _await(world.issues.save(_seed_issue()))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.get(
            "/api/v3/issues",
            params={"organization_id": "org-a", "limit": 9999},
        )
        assert resp.status_code == 422
        resp = client.get(
            "/api/v3/issues",
            params={"organization_id": "org-a", "limit": 0},
        )
        assert resp.status_code == 422
        resp = client.get(
            "/api/v3/issues",
            params={"organization_id": "org-a", "offset": -1},
        )
        assert resp.status_code == 422

    def test_update_status_transition(self, world: InMemoryWorld, client, user_provider) -> None:
        _await(world.issues.save(_seed_issue()))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put("/api/v3/issues/issue-1", json={"status": "resolved"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    def test_reopen_stamps_reopened_at(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        _await(world.issues.save(_seed_issue()))
        _await(world.issues.update_status("issue-1", "closed", updated_by="member-1"))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put("/api/v3/issues/issue-1", json={"status": "open"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "open"
        assert body["reopened_at"] is not None

    def test_invalid_transition_rejected(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        _await(world.issues.save(_seed_issue()))
        _await(world.issues.update_status("issue-1", "closed", updated_by="member-1"))
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        # closed -> in_progress is not a permitted transition.
        resp = client.put("/api/v3/issues/issue-1", json={"status": "in_progress"})
        assert resp.status_code == 409

    def test_entity_issue_listing(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        _await(world.entities.save(ProcessingEntity(id="pe-1", name="Babui")))
        _await(world.issues.save(
            Issue(id="issue-entity", title="Entity issue", entity_id="pe-1", status="open")
        ))
        entity_staff = member_user("org-a", "entity-staff", "e@test")
        entity_staff.is_staff = True
        entity_staff.entity_id = "pe-1"
        user_provider.set_user(entity_staff)
        resp = client.get("/api/v3/issues/admin/entity/pe-1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["issues"][0]["entity_id"] == "pe-1"

    def test_entity_issue_listing_denied_for_other_entity(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        _await(world.entities.save(ProcessingEntity(id="pe-1", name="Babui")))
        entity_staff = member_user("org-a", "entity-staff", "e@test")
        entity_staff.is_staff = True
        entity_staff.entity_id = "pe-2"
        user_provider.set_user(entity_staff)
        resp = client.get("/api/v3/issues/admin/entity/pe-1")
        assert resp.status_code == 403

    def test_entity_issue_listing_denied_when_entity_suspended(
        self, world: InMemoryWorld, client, user_provider
    ) -> None:
        """F1 — entity staff lose issues read access once their entity leaves active."""
        _await(
            world.entities.save(
                ProcessingEntity(id="pe-1", name="Babui", status="suspended")
            )
        )
        entity_staff = member_user("org-a", "entity-staff", "e@test")
        entity_staff.is_staff = True
        entity_staff.entity_id = "pe-1"
        user_provider.set_user(entity_staff)
        resp = client.get("/api/v3/issues/admin/entity/pe-1")
        assert resp.status_code == 403

    def test_admin_open_triage(self, world: InMemoryWorld, client) -> None:
        _await(world.issues.save(_seed_issue()))
        _await(world.issues.save(
            Issue(id="issue-closed", title="Done", organization_id="org-a", status="closed")
        ))
        # admin_user is the conftest default; assert only open issues returned.
        resp = client.get("/api/v3/issues/admin/open")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
