"""FIN-06 — Manual Processing Governance API tests.

Covers the ratified control model end-to-end at the API boundary:
* OFF by default (fail closed) and enforced server-side;
* ONLY CarbonTally Admin may change the governance plane;
* organisations / organisation admins / consultants cannot self-enable;
* scope vocabulary + most-specific-wins precedence;
* disabling invalidates QUEUED (``open``) batches and leaves running work alone;
* every change is audited through the existing audit infrastructure.
"""
from __future__ import annotations

import asyncio

from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_admin_user,
    staff_user,
)

ADMIN_BASE = "/api/v3/admin/manual-processing"


def _seed_internal_admin(
    world, *, user_id: str = "u-admin", can_manage_organizations: bool = True
) -> None:
    """Seed an ACTIVE internal CarbonTally admin staff profile + role."""
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(
        StaffRole(
            id="role-fin06",
            name="system_admin",
            permissions={
                "can_manage_organizations": can_manage_organizations,
                "can_manage_staff": True,
            },
        )
    )
    asyncio.run(
        world.staff.save(
            StaffProfile(
                id="sp-fin06",
                user_id=user_id,
                first_name="Admin",
                last_name="One",
                email="admin@carbontally.test",
                role_id="role-fin06",
            )
        )
    )


def _create_batch(client, organization_id: str = "org-a"):
    return client.post(
        f"/api/v3/manual-extraction/batches?organization_id={organization_id}",
        json={"batch_name": "FIN-06 batch"},
    )


class TestManualProcessingDefaultOff:
    def test_org_admin_cannot_create_manual_work_without_a_grant(
        self, client, user_provider
    ) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = _create_batch(client)
        assert resp.status_code == 403
        assert "administrator" in resp.text, resp.text

    def test_org_member_cannot_create_manual_work_without_a_grant(
        self, client, user_provider
    ) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        # require_org_admin() rejects a plain member first (403 either way).
        assert _create_batch(client).status_code == 403


class TestGovernanceIsAdminOnly:
    def test_org_admin_cannot_change_governance(self, client, user_provider) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "enabled": True,
                "reason": "self-enable attempt",
            },
        )
        assert resp.status_code == 403

    def test_org_member_cannot_read_governance(self, client, user_provider) -> None:
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        assert client.get(f"{ADMIN_BASE}/grants").status_code == 403

    def test_consultant_cannot_change_governance(
        self, world, client, user_provider
    ) -> None:
        world.consultants.seed_profile("firm-1", "consultant-1", "Net Zero Advisory")
        world.consultants.seed_firm_member(
            "firm-1", "consultant-1", role="owner", can_manage_clients=True
        )
        user_provider.set_user(consultant_user("consultant-1", "consultant@test"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={
                "scope_type": "consultant_firm",
                "scope_id": "firm-1",
                "enabled": True,
            },
        )
        assert resp.status_code == 403

    def test_internal_staff_without_the_admin_permission_is_denied(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world, user_id="u-op", can_manage_organizations=False)
        user_provider.set_user(staff_user("u-op", role_name="admin"))
        assert client.get(f"{ADMIN_BASE}/grants").status_code == 403


class TestGrantLifecycle:
    def test_admin_enables_an_organization_then_org_work_is_permitted(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))

        grant = client.put(
            f"{ADMIN_BASE}/grants",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "enabled": True,
                "reason": "PO-approved pilot",
            },
        )
        assert grant.status_code == 200
        assert grant.json()["grant"]["enabled"] is True
        assert grant.json()["previous"]["source_level"] == "default"

        actions = [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)
        assert "manual_processing:grant_set" in actions

        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert _create_batch(client).status_code == 201

    def test_disable_overrides_the_broader_grant_and_cancels_queued_work(
        self, world, client, user_provider
    ) -> None:
        running = asyncio.run(
            world.manual_extraction.create_batch(org_id="org-a", batch_name="running")
        )
        asyncio.run(world.manual_extraction.update_batch(running.id, status="in_progress"))
        queued = asyncio.run(
            world.manual_extraction.create_batch(org_id="org-a", batch_name="queued")
        )
        assert queued.status == "open"

        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": False},
        )
        assert resp.status_code == 200
        assert resp.json()["cancelled_batches"] == [queued.id]
        assert resp.json()["running_jobs_left_to_finish"] is True

        # The queued batch is cancelled; the running one is untouched.
        assert asyncio.run(world.manual_extraction.get_batch(queued.id)).status == "cancelled"
        assert asyncio.run(world.manual_extraction.get_batch(running.id)).status == (
            "in_progress"
        )

        actions = [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)
        assert "manual_processing:queued_batches_cancelled" in actions
        assert "manual_processing:grant_set" in actions

    def test_removing_a_grant_falls_back_to_default_deny(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": True},
        )
        removed = client.delete(f"{ADMIN_BASE}/grants/organization/org-a")
        assert removed.status_code == 200
        assert removed.json()["removed"] is True

        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert _create_batch(client).status_code == 403

    def test_unknown_scope_type_is_rejected(self, world, client, user_provider) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "global", "scope_id": "org-a", "enabled": True},
        )
        assert resp.status_code == 422

    def test_effective_endpoint_reports_the_deciding_scope_level(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "consultant_firm", "scope_id": "firm-1", "enabled": True},
        )
        resp = client.get(
            f"{ADMIN_BASE}/effective/org-a?consultant_firm_id=firm-1"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert body["source_level"] == "explicit"
        assert body["source_scope_type"] == "consultant_firm"

    def test_internal_staff_operator_is_not_blocked_by_customer_governance(
        self, world, client, user_provider
    ) -> None:
        """CarbonTally internal staff act as the platform operator (documented
        interpretation): they keep their existing staff permission gating and are
        not gated by a customer-scope governance row."""
        _seed_internal_admin(world, can_manage_organizations=False)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        assert _create_batch(client).status_code == 201
