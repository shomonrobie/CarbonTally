"""CT-MP-SUB-004 — production-readiness remediations (F-7, F-9, F-11, NV-9, NV-10).

Covers the PO-authorized production-readiness items for the Manual Processing
coverage surfaces:

* **F-7**  allocation error fidelity — only the EXPECTED duplicate/capacity
           refusal is a 409; any other failure is a genuine server error;
* **F-9**  idempotency / concurrency — deterministic duplicate + release
           behaviour and a capacity guard re-checked atomically;
* **F-11** the read-only, name-searchable Admin client lookup that replaces
           manual organisation-id entry;
* **NV-9** the batched organisation-name resolution (no N+1);
* **NV-10** the documented audit-only notification behaviour.

No database is touched: the in-memory fakes only. The client fixture keeps
``raise_server_exceptions=True`` on purpose — an unexpected server-side failure
PROPAGATES rather than being flattened into a 409, which is exactly the F-7
property under test.
"""
from __future__ import annotations

import asyncio

import pytest

from domain.manual_processing import (
    CapacityExceededError,
    DuplicateActiveAllocationError,
)
from tests.unit.api.fakes import consultant_user, org_admin_user, staff_user

ADMIN_BASE = "/api/v3/admin/manual-processing"
CONSULTANT_ALLOC = "/api/v3/consultants/me/manual-processing/allocations"
CONSULTANT_COVERAGE = "/api/v3/consultants/me/manual-processing/coverage"
ADMIN_ALLOC = f"{ADMIN_BASE}/coverage/allocations"
ADMIN_COVERAGE = f"{ADMIN_BASE}/coverage"
ADMIN_ORGS = f"{ADMIN_BASE}/organizations"


# ---------------------------------------------------------------------------
# Seeding helpers (firm-scoped commercial model over the fakes)
# ---------------------------------------------------------------------------


def _seed_internal_admin(world, *, user_id: str = "u-admin") -> None:
    """CarbonTally internal staff holding the admin-grade capability."""
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


def _as_admin(world, user_provider, *, user_id: str = "u-admin") -> None:
    _seed_internal_admin(world, user_id=user_id)
    user_provider.set_user(staff_user(user_id, role_name="admin"))


def _seed_sponsoring_firm(
    world,
    *,
    mode: str = "SELECTED_CLIENTS",
    capacity: int | None = 10,
    firm: str = "firm-1",
    firm_org: str = "firm-org",
    company_name: str = "Acme Consultants",
    client_orgs: tuple[str, ...] = ("org-a",),
) -> None:
    world.consultants.seed_profile(
        firm, "u-c", company_name=company_name, organization_id=firm_org
    )
    world.manual_processing.seed_firm_organization(firm, firm_org)
    world.manual_processing.seed_firm_coverage(firm, mode=mode, capacity=capacity)
    for org in client_orgs:
        world.consultants.seed_client(
            f"cc-{org}", firm, org, f"Client {org[-1].upper()}", status="active"
        )
        world.manual_processing.seed_active_client_grant(org, firm)
        world.manual_processing.seed_eligible_client(firm, org)


def _as_consultant(
    world, user_provider, *, can_manage_clients: bool = True, user_id: str = "u-c"
):
    world.consultants.seed_firm_member(
        "firm-1", user_id, role="owner", can_manage_clients=can_manage_clients
    )
    user_provider.set_user(consultant_user(user_id, "consultant@carbontally.test"))


def _audit_actions(world) -> list[str]:
    return [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)


# ---------------------------------------------------------------------------
# F-7 — allocation error fidelity
# ---------------------------------------------------------------------------


class TestF7AllocationErrorFidelity:
    """Only the EXPECTED refusal is a 409; everything else is a real error."""

    def test_successful_allocation_returns_200(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["allocation"]["state"] == "active"

    def test_legitimate_duplicate_is_409(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        first = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert first.status_code == 200, first.text
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 409, resp.text
        assert "already has an active" in resp.text.lower()
        active = asyncio.run(
            world.manual_processing.list_allocations(
                consultant_id="firm-1", state="active"
            )
        )
        assert len(active) == 1

    def test_invalid_request_is_422(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        assert client.post(CONSULTANT_ALLOC, json={}).status_code == 422
        bogus = client.post(
            CONSULTANT_ALLOC, json={"organization_id": "org-a", "bogus": 1}
        )
        assert bogus.status_code == 422

    def test_unauthenticated_is_401(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        user_provider.set_unauthenticated()
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 401

    def test_missing_capability_is_403(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider, can_manage_clients=False)
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 403

    def test_foreign_organisation_is_403(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-b"})
        assert resp.status_code == 403, resp.text

    def test_unexpected_failure_is_not_reported_as_a_duplicate(
        self, world, client, user_provider
    ):
        """F-7 — a genuine infrastructure failure must NOT become a 409."""
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)

        async def _boom(**kwargs):
            raise RuntimeError("database connection lost")

        world.manual_processing.create_allocation = _boom  # type: ignore[assignment]

        # raise_server_exceptions=True ⇒ the real error propagates (HTTP 500 in
        # production) instead of being flattened into a misleading 409.
        with pytest.raises(RuntimeError):
            client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})

    def test_admin_unexpected_failure_is_not_reported_as_a_duplicate(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5)
        _as_admin(world, user_provider)

        async def _boom(**kwargs):
            raise RuntimeError("database connection lost")

        world.manual_processing.create_allocation = _boom  # type: ignore[assignment]
        with pytest.raises(RuntimeError):
            client.post(
                ADMIN_ALLOC,
                json={"consultant_id": "firm-1", "organization_id": "org-a"},
            )

    def test_admin_duplicate_is_409(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=5)
        _as_admin(world, user_provider)
        body = {"consultant_id": "firm-1", "organization_id": "org-a"}
        assert client.post(ADMIN_ALLOC, json=body).status_code == 200
        assert client.post(ADMIN_ALLOC, json=body).status_code == 409


# ---------------------------------------------------------------------------
# F-9 — idempotency / concurrency
# ---------------------------------------------------------------------------


class TestF9IdempotencyAndConcurrency:
    def test_repeated_equivalent_allocation_is_refused_once_only(
        self, world, client, user_provider
    ):
        """Browser/network retry ⇒ exactly one allocation, deterministic 409."""
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        codes = [
            client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"}).status_code
            for _ in range(3)
        ]
        assert codes == [200, 409, 409], codes
        active = asyncio.run(
            world.manual_processing.list_allocations(
                consultant_id="firm-1", state="active"
            )
        )
        assert len(active) == 1

    def test_release_is_deterministic_and_leaves_others_untouched(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5, client_orgs=("org-a", "org-b"))
        _as_consultant(world, user_provider)
        a = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"}).json()
        b = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-b"}).json()

        first = client.delete(f"{CONSULTANT_ALLOC}/{a['allocation']['id']}")
        assert first.status_code == 200, first.text
        again = client.delete(f"{CONSULTANT_ALLOC}/{a['allocation']['id']}")
        assert again.status_code == 404, again.text

        b_active = asyncio.run(
            world.manual_processing.get_active_allocation(
                consultant_id="firm-1", organization_id="org-b"
            )
        )
        assert b_active is not None
        assert b_active.id == b["allocation"]["id"]

    def test_releasing_a_foreign_allocation_is_denied(
        self, world, client, user_provider
    ):
        """A cross-firm allocation id must never be released silently."""
        _seed_sponsoring_firm(world, capacity=5)
        foreign = world.manual_processing.seed_allocation("firm-2", "org-b")
        _as_consultant(world, user_provider)
        resp = client.delete(f"{CONSULTANT_ALLOC}/{foreign.id}")
        assert resp.status_code == 404, resp.text
        still = asyncio.run(
            world.manual_processing.get_active_allocation(
                consultant_id="firm-2", organization_id="org-b"
            )
        )
        assert still is not None, "a foreign allocation must remain active"

    def test_allocation_at_capacity_is_refused(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=1, client_orgs=("org-a", "org-b"))
        _as_consultant(world, user_provider)
        first = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert first.status_code == 200, first.text
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-b"})
        assert resp.status_code == 409, resp.text
        assert "capacity" in resp.text.lower()

    def test_allocation_below_capacity_succeeds(self, world, client, user_provider):
        _seed_sponsoring_firm(world, capacity=3, client_orgs=("org-a", "org-b"))
        _as_consultant(world, user_provider)
        first = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        second = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-b"})
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text

    def test_capacity_is_re_checked_inside_the_allocation_transaction(
        self, world, client, user_provider
    ):
        """The API must pass the server-derived capacity to the atomic guard.

        This is the wiring proof for the DB-level advisory lock: the endpoint
        does not rely on its own cheap pre-check alone.
        """
        _seed_sponsoring_firm(world, capacity=4)
        _as_consultant(world, user_provider)
        seen: dict = {}
        original = world.manual_processing.create_allocation

        async def _spy(**kwargs):
            seen.update(kwargs)
            return await original(**kwargs)

        world.manual_processing.create_allocation = _spy  # type: ignore[assignment]
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 200, resp.text
        assert seen.get("capacity") == 4, seen

    def test_capacity_consumed_by_a_concurrent_writer_is_refused(
        self, world, client, user_provider
    ):
        """A lost race must surface as a deterministic 409, never a 500 or a
        silent over-allocation.

        The pre-check here reports spare capacity (the state the caller read),
        while the atomic guard refuses because a concurrent request consumed the
        last unit. The API must translate ONLY that typed refusal to 409.
        """
        _seed_sponsoring_firm(world, capacity=1, client_orgs=("org-a", "org-b"))
        _as_consultant(world, user_provider)

        async def _race_lost(**kwargs):
            raise CapacityExceededError("selected-client capacity is exhausted")

        world.manual_processing.create_allocation = _race_lost  # type: ignore[assignment]
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 409, resp.text
        assert "exhausted" in resp.text.lower()

    def test_concurrent_equivalent_requests_serialise_to_one_row(
        self, world, client, user_provider
    ):
        """Model the concurrent double-submit with two independent requests.

        The in-memory fake is sequential, so this asserts the CONTRACT every
        concurrent caller must observe: the first wins, every later equivalent
        request is refused with 409 and no second row is created. The DB
        enforcement behind that contract (a per-firm ``pg_advisory_xact_lock``
        plus the partial unique index) lives in ``data/manual_processing`` and is
        exercised against the Demo Lab database — see the report §7.
        """
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        results = [
            client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"}).status_code
            for _ in range(2)
        ]
        assert sorted(results) == [200, 409], results
        active = asyncio.run(
            world.manual_processing.list_allocations(
                consultant_id="firm-1", state="active"
            )
        )
        assert len(active) == 1

    def test_duplicate_and_capacity_are_typed_refusals(self):
        """The typed refusal vocabulary the API maps to 409."""
        assert issubclass(DuplicateActiveAllocationError, Exception)
        assert issubclass(CapacityExceededError, Exception)


# ---------------------------------------------------------------------------
# F-11 — Admin client selection
# ---------------------------------------------------------------------------


class TestF11AdminClientSelection:
    def test_search_returns_named_organisations(self, world, client, user_provider):
        _as_admin(world, user_provider)
        resp = client.get(ADMIN_ORGS, params={"q": "Org"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        ids = {o["id"] for o in body["organizations"]}
        assert {"org-a", "org-b"} <= ids
        for org in body["organizations"]:
            assert org["name"], "every result must carry a human-readable name"

    def test_search_filters_by_name(self, world, client, user_provider):
        _as_admin(world, user_provider)
        body = client.get(ADMIN_ORGS, params={"q": "Org A"}).json()
        assert [o["id"] for o in body["organizations"]] == ["org-a"]
        assert body["total"] == 1

    def test_search_with_no_match_returns_an_empty_result(
        self, world, client, user_provider
    ):
        _as_admin(world, user_provider)
        body = client.get(ADMIN_ORGS, params={"q": "zzz-no-such-org"}).json()
        assert body["organizations"] == []
        assert body["total"] == 0

    def test_search_is_bounded(self, world, client, user_provider):
        _as_admin(world, user_provider)
        assert client.get(ADMIN_ORGS, params={"limit": 500}).status_code == 422

    def test_search_requires_the_manual_processing_admin_gate(
        self, world, client, user_provider
    ):
        # A customer identity is not internal staff.
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert client.get(ADMIN_ORGS, params={"q": "Org"}).status_code in (401, 403)

    def test_search_requires_authentication(self, world, client, user_provider):
        user_provider.set_unauthenticated()
        assert client.get(ADMIN_ORGS, params={"q": "Org"}).status_code == 401

    def test_search_performs_no_mutation(self, world, client, user_provider):
        _as_admin(world, user_provider)
        before = list(_audit_actions(world))
        client.get(ADMIN_ORGS, params={"q": "Org"})
        assert _audit_actions(world) == before
        assert (
            asyncio.run(world.manual_processing.list_allocations(consultant_id="firm-1"))
            == []
        )

    def test_admin_coverage_exposes_human_readable_client_names(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5, client_orgs=("org-a",))
        _as_admin(world, user_provider)
        body = client.get(f"{ADMIN_COVERAGE}/firm-1").json()
        assert body["client_names"]["org-a"] == "Org A"

    def test_admin_coverage_for_an_unknown_firm_is_404(
        self, world, client, user_provider
    ):
        _as_admin(world, user_provider)
        assert client.get(f"{ADMIN_COVERAGE}/firm-does-not-exist").status_code == 404


# ---------------------------------------------------------------------------
# NV-9 — bounded name resolution (no N+1)
# ---------------------------------------------------------------------------


class TestNV9NameResolutionBatching:
    def _spies(self, world):
        calls = {"get_many": 0, "get": 0}
        original_many = world.organizations.get_many
        original_get = world.organizations.get

        async def _many(ids):
            calls["get_many"] += 1
            return await original_many(ids)

        async def _get(org_id):
            calls["get"] += 1
            return await original_get(org_id)

        world.organizations.get_many = _many  # type: ignore[assignment]
        world.organizations.get = _get  # type: ignore[assignment]
        return calls

    def test_consultant_coverage_uses_one_batched_name_lookup(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5, client_orgs=("org-a", "org-b"))
        _as_consultant(world, user_provider)
        calls = self._spies(world)
        resp = client.get(CONSULTANT_COVERAGE)
        assert resp.status_code == 200, resp.text
        assert calls["get_many"] == 1, calls
        assert calls["get"] == 0, calls

    def test_admin_coverage_uses_one_batched_name_lookup(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5, client_orgs=("org-a", "org-b"))
        _as_admin(world, user_provider)
        calls = self._spies(world)
        resp = client.get(f"{ADMIN_COVERAGE}/firm-1")
        assert resp.status_code == 200, resp.text
        assert calls["get_many"] == 1, calls
        assert calls["get"] == 0, calls


# ---------------------------------------------------------------------------
# NV-10 — documented notification behaviour (audit-only)
# ---------------------------------------------------------------------------


class TestNV10NotificationBehaviour:
    """Every MP state change leaves a durable AUDIT record and NO user
    notification. This is the documented product behaviour (report §12): a
    proactive allocation/release notification would require a PO + provider
    decision and is deliberately NOT implemented."""

    def _notification_rows(self, world) -> int:
        return len(world.notifications.rows)  # noqa: SLF001 (test fake)

    def test_allocation_records_audit_and_emits_no_notification(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        before = self._notification_rows(world)
        resp = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"})
        assert resp.status_code == 200, resp.text
        assert "manual_processing:allocation_created" in _audit_actions(world)
        assert self._notification_rows(world) == before
        assert "notification" not in resp.text.lower()

    def test_release_records_audit_and_emits_no_notification(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5)
        _as_consultant(world, user_provider)
        alloc = client.post(CONSULTANT_ALLOC, json={"organization_id": "org-a"}).json()
        before = self._notification_rows(world)
        resp = client.delete(f"{CONSULTANT_ALLOC}/{alloc['allocation']['id']}")
        assert resp.status_code == 200, resp.text
        assert "manual_processing:allocation_released" in _audit_actions(world)
        assert self._notification_rows(world) == before

    def test_admin_allocation_records_audit_and_emits_no_notification(
        self, world, client, user_provider
    ):
        _seed_sponsoring_firm(world, capacity=5)
        _as_admin(world, user_provider)
        before = self._notification_rows(world)
        resp = client.post(
            ADMIN_ALLOC, json={"consultant_id": "firm-1", "organization_id": "org-a"}
        )
        assert resp.status_code == 200, resp.text
        assert "manual_processing:allocation_created" in _audit_actions(world)
        assert self._notification_rows(world) == before





