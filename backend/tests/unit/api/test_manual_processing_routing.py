"""Manual Processing — subscription gating, PE configuration and auto-fallback.

Covers the ratified decision chain end-to-end at the API/service boundary:

    subscription entitlement -> Manual Processing eligibility
      -> Admin enablement (FIN-06) -> configured Processing Entity
        -> automatic extraction-failure routing -> PE work-item assignment

All tests run over the in-memory fakes; no database is touched.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from domain.entity import ProcessingEntity
from services.manual_processing_routing import ManualProcessingRouter
from tests.unit.api.fakes import member_user, org_admin_user, staff_user

ADMIN_BASE = "/api/v3/admin/manual-processing"


@dataclass
class _Job:
    """Minimal automatic-processing job stand-in for the fallback router."""

    id: str = "job-1"
    organization_id: str = "org-a"
    stage: str = "blocked"
    manual_review_reason: str | None = "extraction incomplete"
    last_error: str | None = None
    source_item_id: str | None = "item-1"
    file_name: str = "invoice.pdf"


def _seed_internal_admin(
    world, *, user_id: str = "u-admin", can_manage_organizations: bool = True
) -> None:
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(
        StaffRole(
            id="role-mp",
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
                id="sp-mp",
                user_id=user_id,
                first_name="Admin",
                last_name="One",
                email="admin@carbontally.test",
                role_id="role-mp",
            )
        )
    )


def _seed_entity(world, entity_id: str = "pe-1", *, status: str = "active") -> None:
    asyncio.run(
        world.entities.save(
            ProcessingEntity(id=entity_id, name=f"PE {entity_id}", status=status)
        )
    )


def _seed_item(world, *, item_id: str = "item-1", org: str = "org-a"):
    return world.manual_extraction.seed_item(item_id, org, "invoice.pdf")


def _create_batch(client, organization_id: str = "org-a"):
    return client.post(
        f"/api/v3/manual-extraction/batches?organization_id={organization_id}",
        json={"batch_name": "MP batch"},
    )


def _actions(world) -> list[str]:
    return [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)


class TestSubscriptionGating:
    """Subscription is the FIRST gate: eligibility, activation, enforcement."""

    def test_admin_can_enable_when_the_customer_is_entitled(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["grant"]["enabled"] is True

    def test_enabling_without_entitlement_is_rejected(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": True},
        )
        assert resp.status_code == 409, resp.text
        assert "plan" in resp.text.lower()
        assert "manual_processing:grant_rejected_not_entitled" in _actions(world)

    def test_disabling_is_always_allowed(self, world, client, user_provider) -> None:
        """Disabling never needs entitlement (it only reduces capability)."""
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": False},
        )
        assert resp.status_code == 200, resp.text

    def test_stale_enabled_grant_cannot_bypass_missing_entitlement(
        self, world, client, user_provider
    ) -> None:
        """An enabled grant with NO subscription must still deny manual work."""
        world.manual_processing.seed_grant("organization", "org-a")
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = _create_batch(client)
        assert resp.status_code == 403, resp.text
        assert "plan" in resp.text.lower(), resp.text

    def test_entitled_but_disabled_grant_denies_with_enablement_reason(
        self, world, client, user_provider
    ) -> None:
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a", enabled=False)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = _create_batch(client)
        assert resp.status_code == 403, resp.text
        assert "administrator" in resp.text, resp.text

    def test_entitled_and_enabled_permits_the_manual_workflow(
        self, world, client, user_provider
    ) -> None:
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a", enabled=True)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert _create_batch(client).status_code == 201


class TestProcessorConfiguration:
    """Admin-only, entitlement-gated persistent processor configuration."""

    def test_admin_can_assign_a_processor_when_entitled(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        _seed_entity(world, "pe-1")
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-1",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["processor"]["processing_entity_id"] == "pe-1"
        assert "manual_processing:processor_set" in _actions(world)

    def test_processor_assignment_requires_entitlement(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        _seed_entity(world, "pe-1")
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-1",
            },
        )
        assert resp.status_code == 409, resp.text
        assert "manual_processing:processor_rejected_not_entitled" in _actions(world)

    def test_unknown_processing_entity_is_rejected(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-does-not-exist",
            },
        )
        assert resp.status_code == 404, resp.text

    def test_inactive_processing_entity_is_rejected(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        _seed_entity(world, "pe-1", status="suspended")
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-1",
            },
        )
        assert resp.status_code == 409, resp.text

    def test_state_reports_the_missing_processor_explicitly(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a", enabled=True)
        resp = client.get(f"{ADMIN_BASE}/state?scope_type=organization&scope_id=org-a")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["entitlement"]["entitled"] is True
        assert body["effective"]["outcome"] == "no_processor_configured"
        assert body["scope_processor"] is None

    def test_processor_removal_reports_no_destination(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-1"
        )
        removed = client.delete(f"{ADMIN_BASE}/processors/organization/org-a")
        assert removed.status_code == 200, removed.text
        assert removed.json()["removed"] is True


def _route(world, job: "_Job | None" = None) -> dict:
    return asyncio.run(ManualProcessingRouter(world.bundle()).route_failed_job(job or _Job()))


class TestAutomaticFallback:
    """Automatic extraction failure -> configured PE (idempotent)."""

    def test_failure_with_manual_processing_off_creates_no_pe_task(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        # Entitled customer, but an explicit DISABLED governance value.
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a", enabled=False)
        world.manual_processing.seed_processor("organization", "org-a")
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "not_enabled"
        assert asyncio.run(world.manual_extraction.work_item_current("item-1")) is None

    def test_failure_without_subscription_creates_no_pe_task(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        # Enabled grant but the customer has NO Manual Processing subscription.
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor("organization", "org-a")
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "not_entitled"
        assert asyncio.run(world.manual_extraction.work_item_current("item-1")) is None
        assert "manual_processing:auto_route_denied" in _actions(world)

    def test_failure_routes_to_the_configured_processing_entity(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-1"
        )
        outcome = _route(world)
        assert outcome["routed"] is True
        assert outcome["processing_entity_id"] == "pe-1"
        current = asyncio.run(world.manual_extraction.work_item_current("item-1"))
        assert current["assignee_kind"] == "processing_entity"
        assert current["processing_entity_id"] == "pe-1"
        assert "manual_processing:auto_routed" in _actions(world)

    def test_the_routed_item_is_visible_in_the_pe_workspace(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-1"
        )
        _route(world)
        batches = asyncio.run(
            world.manual_extraction.list_batches_with_open_entity_item("pe-1")
        )
        assert [b.id for b in batches] == ["batch-item-1"]

    def test_retry_does_not_create_a_duplicate_assignment(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor("organization", "org-a", processing_entity_id="pe-1")
        first = _route(world)
        second = _route(world)
        assert first["idempotent"] is False
        assert second["idempotent"] is True
        rows = asyncio.run(world.manual_extraction.work_item_history("item-1"))
        assert len(rows) == 1, rows

    def test_worker_restart_does_not_create_a_duplicate_assignment(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor("organization", "org-a", processing_entity_id="pe-1")
        _route(world)
        # A brand-new router instance (fresh worker process) reaches the same
        # conclusion from the persisted single-open assignment.
        outcome = asyncio.run(
            ManualProcessingRouter(world.bundle()).route_failed_job(_Job())
        )
        assert outcome["idempotent"] is True
        rows = asyncio.run(world.manual_extraction.work_item_history("item-1"))
        assert len(rows) == 1, rows

    def test_enabled_but_unconfigured_is_blocked_with_explicit_state(self, world) -> None:
        _seed_item(world)
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "no_processor_configured"
        assert "manual_processing:auto_route_blocked_no_processor" in _actions(world)

    def test_the_existing_manual_workflow_can_continue_after_routing(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor("organization", "org-a", processing_entity_id="pe-1")
        _route(world)
        # The auto-created work item is a normal manual-extraction item: the
        # existing downstream workflow (status transitions) is unchanged.
        asyncio.run(world.manual_extraction.set_item_status("item-1", "extracting"))
        item = asyncio.run(world.manual_extraction.get_item("item-1"))
        assert item.status == "extracting"


class TestConsultantClientRouting:
    """Consultant-client resolution reuses the FIN-06 most-specific-wins model."""

    def _consultant_client_world(self, world) -> None:
        world.manual_processing.set_org_context(
            "org-a", consultant_client_id="cc-1", consultant_firm_id="firm-1"
        )
        # Entitlement stays with the CLIENT organisation (documented P6-2 P0-1):
        # a consultant consumes the client's entitlement, never the firm's.
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("consultant_client", "cc-1")
        _seed_entity(world, "pe-client")
        _seed_entity(world, "pe-org")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-org"
        )
        world.manual_processing.seed_processor(
            "consultant_client", "cc-1", processing_entity_id="pe-client"
        )

    def test_consultant_client_scope_routes_to_the_client_processor(self, world) -> None:
        _seed_item(world, org="org-a")
        self._consultant_client_world(world)
        outcome = _route(world)
        assert outcome["routed"] is True
        assert outcome["processing_entity_id"] == "pe-client"

    def test_a_parent_scope_cannot_bypass_a_client_level_denial(self, world) -> None:
        _seed_item(world, org="org-a")
        self._consultant_client_world(world)
        # The firm scope is enabled, but the more specific CLIENT scope denies.
        world.manual_processing.seed_grant("consultant_firm", "firm-1")
        world.manual_processing.seed_grant("consultant_client", "cc-1", enabled=False)
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "not_enabled"


class TestSecurityBoundaries:
    """Every Manual Processing rule is enforced server-side."""

    def test_a_customer_cannot_enable_manual_processing(
        self, world, client, user_provider
    ) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={"scope_type": "organization", "scope_id": "org-a", "enabled": True},
        )
        assert resp.status_code == 403, resp.text

    def test_a_customer_cannot_assign_a_processor(
        self, world, client, user_provider
    ) -> None:
        _seed_entity(world, "pe-1")
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-1",
            },
        )
        assert resp.status_code == 403, resp.text

    def test_a_forged_entitlement_field_in_the_payload_is_rejected(
        self, world, client, user_provider
    ) -> None:
        """Entitlement is never accepted from the request body."""
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.put(
            f"{ADMIN_BASE}/grants",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "enabled": True,
                "entitled": True,
                "assisted_processing_available": True,
            },
        )
        assert resp.status_code == 422, resp.text

    def test_a_forged_processor_field_in_the_payload_is_rejected(
        self, world, client, user_provider
    ) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        world.manual_processing.seed_entitlement("org-a")
        resp = client.put(
            f"{ADMIN_BASE}/processors",
            json={
                "scope_type": "organization",
                "scope_id": "org-a",
                "processing_entity_id": "pe-1",
                "validate": False,
            },
        )
        assert resp.status_code == 422, resp.text

    def test_processor_listing_is_admin_only(self, world, client, user_provider) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert client.get(f"{ADMIN_BASE}/processors").status_code == 403
