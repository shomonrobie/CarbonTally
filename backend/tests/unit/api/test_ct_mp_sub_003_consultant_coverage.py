"""CT-MP-SUB-003 — consultant-sponsored Manual Processing coverage (API/service).

Covers the ratified commercial model end-to-end over the in-memory fakes:

    ELIGIBILITY (consultant_client relationship)
      + COMMERCIAL COVERAGE (firm's own org subscription plan)
        -> sponsored entitlement (selected capacity OR all eligible)
          OR direct entitlement
            -> FIN-06 governance -> configured PE -> routing

No database is touched. Mapped to the PO spec §19 acceptance scenarios.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from domain.entity import ProcessingEntity
from services.manual_processing_routing import ManualProcessingRouter
from tests.unit.api.fakes import org_admin_user, staff_user

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


def _seed_internal_admin(world, *, user_id: str = "u-admin") -> None:
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(
        StaffRole(
            id="role-mp",
            name="system_admin",
            permissions={
                "can_manage_organizations": True,
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


def _route(world, job: "_Job | None" = None) -> dict:
    return asyncio.run(
        ManualProcessingRouter(world.bundle()).route_failed_job(job or _Job())
    )


def _actions(world) -> list[str]:
    return [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)


def _sponsor(
    world,
    *,
    mode,
    capacity=None,
    firm: str = "firm-1",
    firm_org: str = "firm-org",
    client_orgs=("org-a",),
) -> None:
    """Seed a sponsoring consultant firm with eligible client organisations."""
    world.manual_processing.seed_firm_organization(firm, firm_org)
    world.manual_processing.seed_firm_coverage(firm, mode=mode, capacity=capacity)
    for org in client_orgs:
        world.manual_processing.seed_active_client_grant(org, firm)
        world.manual_processing.seed_eligible_client(firm, org)


class TestEntitlementResolution:
    """DIRECT + SPONSORED resolution over the existing commercial model."""

    def _router(self, world) -> ManualProcessingRouter:
        return ManualProcessingRouter(world.bundle())

    def test_direct_entitlement_from_own_subscription(self, world) -> None:
        world.manual_processing.seed_entitlement("org-a")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.direct_entitled is True
        assert decision.sponsored_entitled is False

    def test_relationship_alone_is_not_an_entitlement(self, world) -> None:
        """A consultant-client relationship never grants Manual Processing."""
        world.manual_processing.seed_active_client_grant("org-a", "firm-1")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is False
        assert decision.sponsored_entitled is False

    def test_all_eligible_sponsors_an_eligible_client(self, world) -> None:
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.source == "sponsored"
        assert decision.sponsored_mode == "ALL_ELIGIBLE_CLIENTS"

    def test_all_eligible_does_not_cover_an_unrelated_organisation(self, world) -> None:
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS", client_orgs=("org-a",))
        decision = asyncio.run(self._router(world).entitlement_for("org-unrelated"))
        assert decision.entitled is False

    def test_selected_requires_an_active_allocation(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10)
        router = self._router(world)
        assert asyncio.run(router.entitlement_for("org-a")).entitled is False
        world.manual_processing.seed_allocation("firm-1", "org-a")
        decision = asyncio.run(router.entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.sponsored_reason == "selected_allocated"

    def test_direct_and_sponsored_are_combined(self, world) -> None:
        world.manual_processing.seed_entitlement("org-a")
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.source == "direct+sponsored"
        assert decision.direct_entitled is True
        assert decision.sponsored_entitled is True

    def test_sponsored_ends_while_direct_remains(self, world) -> None:
        """Direct active + sponsored inactive -> still entitled (direct path)."""
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_active_client_grant("org-a", "firm-1")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.source == "feature"

    def test_direct_ends_while_sponsored_remains(self, world) -> None:
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is True
        assert decision.source == "sponsored"

    def test_both_paths_inactive_is_not_entitled(self, world) -> None:
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is False
        assert decision.source == "none"

    def test_inactive_consultant_subscription_grants_no_coverage(self, world) -> None:
        """A relationship with NO qualifying firm subscription is not sponsored."""
        world.manual_processing.seed_firm_organization("firm-1", "firm-org")
        world.manual_processing.seed_active_client_grant("org-a", "firm-1")
        decision = asyncio.run(self._router(world).entitlement_for("org-a"))
        assert decision.entitled is False
        assert decision.sponsored_reason == "no_coverage"


class TestSelectedCapacityLifecycle:
    """Finite selected capacity: consume / exhaust / release / reuse / upgrade."""

    def _router(self, world) -> ManualProcessingRouter:
        return ManualProcessingRouter(world.bundle())

    def _state(self, world, firm: str = "firm-1") -> dict:
        return asyncio.run(self._router(world).coverage_state_for_firm(firm))

    def test_selected_seven_of_ten(self, world) -> None:
        orgs = tuple(f"org-{i}" for i in range(7))
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10, client_orgs=orgs)
        for org in orgs:
            world.manual_processing.seed_allocation("firm-1", org)
        state = self._state(world)
        assert state["capacity"] == 10
        assert state["allocated"] == 7
        assert state["available"] == 3
        assert state["over_allocated"] == 0

    def test_selected_ten_of_ten_is_full(self, world) -> None:
        orgs = tuple(f"org-{i}" for i in range(10))
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10, client_orgs=orgs)
        for org in orgs:
            world.manual_processing.seed_allocation("firm-1", org)
        state = self._state(world)
        assert state["allocated"] == 10
        assert state["available"] == 0

    def test_new_client_with_available_capacity(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10, client_orgs=("org-a", "org-b"))
        router = self._router(world)
        assert asyncio.run(router.entitlement_for("org-b")).entitled is False
        world.manual_processing.seed_allocation("firm-1", "org-b")
        assert asyncio.run(router.entitlement_for("org-b")).entitled is True

    def test_new_client_with_exhausted_capacity_is_not_covered(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=1, client_orgs=("org-a", "org-b"))
        world.manual_processing.seed_allocation("firm-1", "org-a")
        state = self._state(world)
        assert state["available"] == 0
        assert asyncio.run(self._router(world).entitlement_for("org-b")).entitled is False

    def test_release_returns_and_reuses_capacity(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=1, client_orgs=("org-a", "org-b"))
        alloc = world.manual_processing.seed_allocation("firm-1", "org-a")
        assert self._state(world)["available"] == 0
        asyncio.run(
            world.manual_processing.release_allocation(
                allocation_id=alloc.id, reason="client left", actor_id="u-admin"
            )
        )
        assert self._state(world)["available"] == 1
        world.manual_processing.seed_allocation("firm-1", "org-b")
        assert asyncio.run(self._router(world).entitlement_for("org-b")).entitled is True

    def test_capacity_upgrade_keeps_existing_allocations(self, world) -> None:
        orgs = tuple(f"org-{i}" for i in range(10))
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10, client_orgs=orgs)
        for org in orgs:
            world.manual_processing.seed_allocation("firm-1", org)
        assert self._state(world)["available"] == 0
        world.manual_processing.set_firm_coverage(
            "firm-1", mode="SELECTED_CLIENTS", capacity=25
        )
        state = self._state(world)
        assert state["capacity"] == 25
        assert state["allocated"] == 10
        assert state["available"] == 15

    def test_selected_downgrade_over_allocation_is_detected(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=25)
        for i in range(22):
            world.manual_processing.seed_allocation("firm-1", f"org-{i}")
        world.manual_processing.set_firm_coverage(
            "firm-1", mode="SELECTED_CLIENTS", capacity=10
        )
        state = self._state(world)
        assert state["over_allocated"] == 12
        assert state["available"] == 0
        # No allocation was silently removed.
        assert state["allocated"] == 22


class TestCoverageStateTransitions:
    """Selected <-> all transitions preserve allocation history (PO spec §7, §8)."""

    def _router(self, world) -> ManualProcessingRouter:
        return ManualProcessingRouter(world.bundle())

    def _state(self, world, firm: str = "firm-1") -> dict:
        return asyncio.run(self._router(world).coverage_state_for_firm(firm))

    def test_selected_to_all_preserves_allocations_and_covers_all(self, world) -> None:
        _sponsor(world, mode="SELECTED_CLIENTS", capacity=10, client_orgs=("org-a", "org-b"))
        world.manual_processing.seed_allocation("firm-1", "org-a")
        world.manual_processing.set_firm_coverage("firm-1", mode="ALL_ELIGIBLE_CLIENTS")
        state = self._state(world)
        assert state["mode"] == "ALL_ELIGIBLE_CLIENTS"
        assert any(a["state"] == "active" for a in state["allocations"])
        # An unallocated eligible client is now covered automatically.
        assert asyncio.run(self._router(world).entitlement_for("org-b")).entitled is True

    def test_all_to_selected_requires_reconciliation(self, world) -> None:
        _sponsor(
            world,
            mode="ALL_ELIGIBLE_CLIENTS",
            client_orgs=("org-a", "org-b", "org-c"),
        )
        world.manual_processing.set_firm_coverage(
            "firm-1", mode="SELECTED_CLIENTS", capacity=1
        )
        state = self._state(world)
        assert state["mode"] == "SELECTED_CLIENTS"
        assert state["capacity"] == 1
        # No client was silently allocated OR silently disabled.
        assert state["allocated"] == 0
        assert sorted(state["unallocated_eligible_clients"]) == ["org-a", "org-b", "org-c"]

    def test_relationship_termination_ends_all_eligible_coverage(self, world) -> None:
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS", client_orgs=("org-a", "org-b"))
        assert asyncio.run(self._router(world).entitlement_for("org-a")).entitled is True
        world.manual_processing.end_client_relationship("org-a", "firm-1")
        assert asyncio.run(self._router(world).entitlement_for("org-a")).entitled is False
        # Other clients are unaffected.
        assert asyncio.run(self._router(world).entitlement_for("org-b")).entitled is True


class TestOperationalIntegration:
    """FIN-06 governance + PE routing remain SEPARATE from commercial entitlement."""

    def test_entitled_and_enabled_but_no_pe_is_no_processor_configured(self, world) -> None:
        _seed_item(world)
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        world.manual_processing.seed_grant("organization", "org-a")
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "no_processor_configured"

    def test_entitled_enabled_and_pe_configured_routes(self, world) -> None:
        _seed_item(world)
        _seed_entity(world, "pe-1")
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-1"
        )
        outcome = _route(world)
        assert outcome["routed"] is True
        assert outcome["processing_entity_id"] == "pe-1"
        assert "manual_processing:auto_routed" in _actions(world)

    def test_fin06_disabled_denies_even_when_sponsored(
        self, world, client, user_provider
    ) -> None:
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.post(
            "/api/v3/manual-extraction/batches?organization_id=org-a",
            json={"batch_name": "MP batch"},
        )
        assert resp.status_code == 403, resp.text
        assert "administrator" in resp.text

    def test_existing_human_assignment_is_preserved(self, world) -> None:
        """An open human assignment is never silently superseded (PO spec §17)."""
        _seed_item(world)
        _seed_entity(world, "pe-1")
        _sponsor(world, mode="ALL_ELIGIBLE_CLIENTS")
        world.manual_processing.seed_grant("organization", "org-a")
        world.manual_processing.seed_processor(
            "organization", "org-a", processing_entity_id="pe-1"
        )
        asyncio.run(
            world.manual_extraction.work_item_open(
                item_id="item-1",
                action="assign",
                assignee_kind="internal_staff",
                assigned_to="u-human",
                processing_entity_id=None,
                actor="u-admin",
                actor_domain="internal_staff",
                reason="manual triage",
                close_action=None,
            )
        )
        outcome = _route(world)
        assert outcome["routed"] is False
        assert outcome["reason"] == "human_assignment_preserved"
        current = asyncio.run(world.manual_extraction.work_item_current("item-1"))
        assert current["assignee_kind"] == "internal_staff"
        assert current["assigned_to"] == "u-human"


class TestAdminCoverageApi:
    """Admin coverage + allocation control plane (server-enforced)."""

    def _admin(self, world, user_provider) -> None:
        _seed_internal_admin(world)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))

    def _firm_with_selected(self, world, capacity: int = 10) -> None:
        world.consultants.seed_profile("firm-1", "u-c", organization_id="firm-org")
        world.manual_processing.seed_firm_organization("firm-1", "firm-org")
        world.manual_processing.seed_firm_coverage(
            "firm-1", mode="SELECTED_CLIENTS", capacity=capacity
        )
        world.consultants.seed_client(
            "cc-a", "firm-1", "org-a", "Client A", status="active"
        )
        world.manual_processing.seed_eligible_client("firm-1", "org-a")

    def test_coverage_endpoint_reports_state(self, world, client, user_provider) -> None:
        self._admin(world, user_provider)
        self._firm_with_selected(world)
        resp = client.get(f"{ADMIN_BASE}/coverage/firm-1")
        assert resp.status_code == 200, resp.text
        cov = resp.json()["coverage"]
        assert cov["mode"] == "SELECTED_CLIENTS"
        assert cov["capacity"] == 10
        assert cov["available"] == 10

    def test_allocate_an_eligible_client(self, world, client, user_provider) -> None:
        self._admin(world, user_provider)
        self._firm_with_selected(world)
        resp = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-a"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["allocation"]["state"] == "active"
        assert resp.json()["coverage"]["allocated"] == 1
        assert "manual_processing:allocation_created" in _actions(world)

    def test_allocation_of_unrelated_organisation_is_denied(
        self, world, client, user_provider
    ) -> None:
        self._admin(world, user_provider)
        self._firm_with_selected(world)
        resp = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-other"},
        )
        assert resp.status_code == 403, resp.text

    def test_allocation_beyond_capacity_is_rejected(
        self, world, client, user_provider
    ) -> None:
        self._admin(world, user_provider)
        self._firm_with_selected(world, capacity=1)
        world.consultants.seed_client(
            "cc-b", "firm-1", "org-b", "Client B", status="active"
        )
        world.manual_processing.seed_eligible_client("firm-1", "org-b")
        first = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-a"},
        )
        assert first.status_code == 200, first.text
        resp = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-b"},
        )
        assert resp.status_code == 409, resp.text
        assert "exhausted" in resp.text.lower()

    def test_release_an_allocation(self, world, client, user_provider) -> None:
        self._admin(world, user_provider)
        self._firm_with_selected(world)
        created = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-a"},
        ).json()["allocation"]["id"]
        resp = client.delete(f"{ADMIN_BASE}/coverage/allocations/{created}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["released"]["state"] == "released"

    def test_allocation_on_all_eligible_coverage_is_rejected(
        self, world, client, user_provider
    ) -> None:
        self._admin(world, user_provider)
        world.consultants.seed_profile("firm-1", "u-c", organization_id="firm-org")
        world.manual_processing.seed_firm_organization("firm-1", "firm-org")
        world.manual_processing.seed_firm_coverage(
            "firm-1", mode="ALL_ELIGIBLE_CLIENTS"
        )
        world.consultants.seed_client(
            "cc-a", "firm-1", "org-a", "Client A", status="active"
        )
        resp = client.post(
            f"{ADMIN_BASE}/coverage/allocations",
            json={"consultant_id": "firm-1", "organization_id": "org-a"},
        )
        assert resp.status_code == 409, resp.text

    def test_client_entitlement_endpoint_reports_all_concepts(
        self, world, client, user_provider
    ) -> None:
        self._admin(world, user_provider)
        world.manual_processing.seed_entitlement("org-a")
        world.consultants.seed_profile("firm-1", "u-c", organization_id="firm-org")
        world.manual_processing.seed_firm_organization("firm-1", "firm-org")
        world.manual_processing.seed_firm_coverage(
            "firm-1", mode="ALL_ELIGIBLE_CLIENTS"
        )
        world.manual_processing.seed_active_client_grant("org-a", "firm-1")
        world.manual_processing.seed_eligible_client("firm-1", "org-a")
        resp = client.get(f"{ADMIN_BASE}/clients/org-a")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["direct"]["entitled"] is True
        assert body["sponsored"]["entitled"] is True
        assert body["effective_entitlement"]["source"] == "direct+sponsored"

    def test_coverage_endpoint_requires_admin(self, world, client, user_provider) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.get(f"{ADMIN_BASE}/coverage/firm-1")
        assert resp.status_code in (401, 403), resp.text




