"""CT-MP-SUB-004 — Manual Processing commercial/entitlement surfaces (API).

The PO-approved UI/UX specification
(``docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md``)
exposes the ratified CT-MP-SUB-003 commercial model to three audiences. The
platform-admin control plane already existed (``api/manual_processing_admin.py``,
covered by ``test_ct_mp_sub_003_consultant_coverage.py``); this module covers the
two ADDITIVE, caller-scoped surfaces:

* Customer   — the caller's OWN organisation effective entitlement
               (``GET /api/v3/organizations/{organization_id}/manual-processing``);
* Consultant — the caller's OWN firm purchased coverage + selected-client
               allocations (``/api/v3/consultants/me/manual-processing/...``).

Every assertion is a SERVER-side property (the browser is never the security
boundary):

* the consultant firm id comes from the authenticated context, never the request;
* capacity / mode / eligibility are re-checked before a write;
* a customer response never reveals a consultant's commercial capacity, another
  client, an allocation id or an internal routing id;
* cross-tenant reads and cross-firm releases are DENIED.

No database is touched: the in-memory fakes only.
"""
from __future__ import annotations

from api.router import router as v3_router
from tests.unit.api.fakes import consultant_user, org_admin_user
from tests.unit.api.route_paths import flatten_router_paths

CUSTOMER_PATH = "/api/v3/organizations/{organization_id}/manual-processing"
CONSULTANT_COVERAGE_PATH = "/api/v3/consultants/me/manual-processing/coverage"
CONSULTANT_ALLOCATIONS_PATH = "/api/v3/consultants/me/manual-processing/allocations"

CUSTOMER_URL = "/api/v3/organizations/org-a/manual-processing"
CONSULTANT_COVERAGE_URL = "/api/v3/consultants/me/manual-processing/coverage"
CONSULTANT_ALLOCATIONS_URL = "/api/v3/consultants/me/manual-processing/allocations"


# ---------------------------------------------------------------------------
# Route exposure — the surfaces the UI/UX spec depends on must be registered
# ---------------------------------------------------------------------------


def test_coverage_routes_are_exposed_on_the_v3_router() -> None:
    paths = flatten_router_paths(v3_router)
    for expected in (
        CUSTOMER_PATH,
        CONSULTANT_COVERAGE_PATH,
        CONSULTANT_ALLOCATIONS_PATH,
        f"{CONSULTANT_ALLOCATIONS_PATH}/{{allocation_id}}",
    ):
        assert expected in paths, f"missing CT-MP-SUB-004 route: {expected}"


# ---------------------------------------------------------------------------
# Shared seeding — the CT-MP-SUB-003 commercial model over the fakes
# ---------------------------------------------------------------------------


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
    """Seed a sponsoring consultant firm with live eligible client organisations."""
    world.consultants.seed_profile(
        firm, "u-c", company_name=company_name, organization_id=firm_org
    )
    world.manual_processing.seed_firm_organization(firm, firm_org)
    world.manual_processing.seed_firm_coverage(firm, mode=mode, capacity=capacity)
    for org in client_orgs:
        # The relationship row the allocation endpoint re-checks (consultant_clients)
        world.consultants.seed_client(
            f"cc-{org}", firm, org, f"Client {org[-1].upper()}", status="active"
        )
        world.manual_processing.seed_active_client_grant(org, firm)
        world.manual_processing.seed_eligible_client(firm, org)


def _seed_consultant(world, *, can_manage_clients: bool = True, user_id: str = "u-c"):
    """Seed the authenticated firm member (the caller) for the consultant surface."""
    world.consultants.seed_firm_member(
        "firm-1",
        user_id,
        role="owner",
        can_manage_clients=can_manage_clients,
    )
    return consultant_user(user_id, "consultant@carbontally.test")


def _audit_actions(world) -> list[str]:
    return [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)


# ---------------------------------------------------------------------------
# Customer — the caller's OWN organisation effective entitlement
# ---------------------------------------------------------------------------


class TestCustomerManualProcessingSurface:
    """Customer-visible Manual Processing service state (org-scoped, read-only)."""

    def _as_customer(self, user_provider, org: str = "org-a") -> None:
        user_provider.set_user(org_admin_user(org, "admin-1", "admin@test"))

    def test_requires_authentication(self, client, user_provider) -> None:
        user_provider.set_unauthenticated()
        resp = client.get(CUSTOMER_URL)
        assert resp.status_code == 401, resp.text

    def test_not_included_when_no_commercial_path_exists(
        self, client, user_provider
    ) -> None:
        """A consultant-client relationship alone is never an entitlement."""
        self._as_customer(user_provider)
        resp = client.get(CUSTOMER_URL)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "not_included"
        assert body["effective_entitled"] is False
        assert body["coverage_sources"] == []
        assert body["consultant"] is None
        assert body["processing_mode"] is None

    def test_direct_entitlement_reports_available(self, world, client, user_provider) -> None:
        world.manual_processing.seed_entitlement("org-a")
        self._as_customer(user_provider)
        body = client.get(CUSTOMER_URL).json()
        assert body["status"] == "available"
        assert body["direct_entitled"] is True
        assert body["coverage_sources"] == ["direct"]
        assert body["processing_mode"] == "manual"

    def test_sponsored_entitlement_names_the_consultant(
        self, world, client, user_provider
    ) -> None:
        _seed_sponsoring_firm(world, mode="ALL_ELIGIBLE_CLIENTS", capacity=None)
        self._as_customer(user_provider)
        body = client.get(CUSTOMER_URL).json()
        assert body["status"] == "available"
        assert body["sponsored_entitled"] is True
        assert body["coverage_sources"] == ["sponsored"]
        assert body["consultant"] == {"company_name": "Acme Consultants"}

    def test_entitled_but_unconfigured_is_not_reported_as_not_subscribed(
        self, world, client, user_provider
    ) -> None:
        """PO UI/UX §10 — entitlement and operational readiness are separate."""
        world.manual_processing.seed_entitlement("org-a")
        self._as_customer(user_provider)
        body = client.get(CUSTOMER_URL).json()
        assert body["effective_entitled"] is True
        assert body["operational_status"] == "not_yet_configured"

    def test_customer_never_sees_consultant_commercial_state(
        self, world, client, user_provider
    ) -> None:
        """Capacity, allocation counts, other clients and ids stay firm-private."""
        _seed_sponsoring_firm(world, mode="SELECTED_CLIENTS", capacity=25)
        world.manual_processing.seed_allocation("firm-1", "org-a")
        self._as_customer(user_provider)
        body = client.get(CUSTOMER_URL).json()
        for leaked in (
            "capacity",
            "allocated",
            "available",
            "over_allocated",
            "allocations",
            "eligible_clients",
            "unallocated_eligible_clients",
            "covered_clients",
            "plan_code",
            "firm_id",
            "firm_organization_id",
            "consultant_id",
            "allocation_id",
        ):
            assert leaked not in body, f"customer response leaked {leaked!r}"

    def test_cannot_read_another_organisation(self, client, user_provider) -> None:
        """F-05-R1 — the path organisation must be the caller's own tenant."""
        self._as_customer(user_provider, org="org-a")
        resp = client.get("/api/v3/organizations/org-b/manual-processing")
        assert resp.status_code == 403, resp.text

    def test_consultant_cannot_read_a_customer_organisation(
        self, world, client, user_provider
    ) -> None:
        """A consultant is not an org member: the customer surface denies them."""
        _seed_sponsoring_firm(world)
        user_provider.set_user(consultant_user("u-c", "c@test"))
        resp = client.get(CUSTOMER_URL)
        assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Consultant — the caller's OWN firm coverage + selected-client allocations
# ---------------------------------------------------------------------------


class TestConsultantManualProcessingSurface:
    """Firm-scoped coverage reads and SELECTED_CLIENTS allocation writes."""

    def _firm(self, world, user_provider, **kwargs):
        _seed_sponsoring_firm(world, **kwargs)
        user_provider.set_user(_seed_consultant(world))
        return world

    def test_coverage_reports_only_the_callers_own_firm(
        self, world, client, user_provider
    ) -> None:
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        resp = client.get(CONSULTANT_COVERAGE_URL)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["consultant_id"] == "firm-1"
        assert body["company_name"] == "Acme Consultants"
        assert body["enabled"] is True
        assert body["mode"] == "SELECTED_CLIENTS"
        assert body["capacity"] == 5
        assert body["allocated"] == 0
        assert body["available"] == 5
        assert body["allocations"] == []
        assert [c["organization_id"] for c in body["eligible_clients"]] == ["org-a"]
        assert body["unallocated_eligible_clients"][0]["organization_id"] == "org-a"

    def test_coverage_names_clients_rather_than_exposing_raw_ids(
        self, world, client, user_provider
    ) -> None:
        """Business context over internal ids (AGENTS.md §37 / §76)."""
        self._firm(world, user_provider)
        body = client.get(CONSULTANT_COVERAGE_URL).json()
        assert body["eligible_clients"][0]["name"], "client name must be resolved"

    def test_requires_consultant_identity(self, world, client, user_provider) -> None:
        self._firm(world, user_provider)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.get(CONSULTANT_COVERAGE_URL)
        assert resp.status_code in (401, 403), resp.text

    def test_allocate_an_eligible_client(self, world, client, user_provider) -> None:
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["allocation"]["state"] == "active"
        assert body["allocation"]["organization_id"] == "org-a"
        assert body["coverage"]["allocated"] == 1
        assert body["coverage"]["available"] == 4
        assert "manual_processing:allocation_created" in _audit_actions(world)

    def test_allocate_requires_the_manage_clients_capability(
        self, world, client, user_provider
    ) -> None:
        _seed_sponsoring_firm(world, mode="SELECTED_CLIENTS", capacity=5)
        user_provider.set_user(_seed_consultant(world, can_manage_clients=False))
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        )
        assert resp.status_code == 403, resp.text

    def test_allocate_an_unrelated_organisation_is_denied(
        self, world, client, user_provider
    ) -> None:
        """A forged organisation id can never consume the firm's capacity."""
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-other"}
        )
        assert resp.status_code == 403, resp.text

    def test_allocate_beyond_capacity_is_rejected(
        self, world, client, user_provider
    ) -> None:
        self._firm(
            world,
            user_provider,
            mode="SELECTED_CLIENTS",
            capacity=1,
            client_orgs=("org-a", "org-b"),
        )
        first = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        )
        assert first.status_code == 200, first.text
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-b"}
        )
        assert resp.status_code == 409, resp.text
        assert "exhausted" in resp.text.lower()

    def test_duplicate_active_allocation_is_rejected(
        self, world, client, user_provider
    ) -> None:
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        payload = {"organization_id": "org-a"}
        assert client.post(CONSULTANT_ALLOCATIONS_URL, json=payload).status_code == 200
        resp = client.post(CONSULTANT_ALLOCATIONS_URL, json=payload)
        assert resp.status_code == 409, resp.text

    def test_allocate_on_all_eligible_coverage_is_rejected(
        self, world, client, user_provider
    ) -> None:
        """ALL_ELIGIBLE_CLIENTS needs no allocation — the write is meaningless."""
        self._firm(world, user_provider, mode="ALL_ELIGIBLE_CLIENTS", capacity=None)
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        )
        assert resp.status_code == 409, resp.text

    def test_allocate_without_purchased_coverage_is_rejected(
        self, world, client, user_provider
    ) -> None:
        world.consultants.seed_profile(
            "firm-1", "u-c", company_name="Acme Consultants", organization_id="firm-org"
        )
        world.manual_processing.seed_firm_organization("firm-1", "firm-org")
        world.consultants.seed_client(
            "cc-a", "firm-1", "org-a", "Client A", status="active"
        )
        user_provider.set_user(_seed_consultant(world))
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        )
        assert resp.status_code == 409, resp.text
        assert "coverage" in resp.text.lower()

    def test_release_an_allocation_returns_the_capacity_unit(
        self, world, client, user_provider
    ) -> None:
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        allocation_id = client.post(
            CONSULTANT_ALLOCATIONS_URL, json={"organization_id": "org-a"}
        ).json()["allocation"]["id"]
        resp = client.delete(f"{CONSULTANT_ALLOCATIONS_URL}/{allocation_id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["released"]["state"] == "released"
        assert body["coverage"]["allocated"] == 0
        assert body["coverage"]["available"] == 5
        assert "manual_processing:allocation_released" in _audit_actions(world)

    def test_release_another_firms_allocation_is_denied(
        self, world, client, user_provider
    ) -> None:
        """Cross-firm release is 404 — never silently released."""
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        other = world.manual_processing.seed_allocation("firm-2", "org-b")
        resp = client.delete(f"{CONSULTANT_ALLOCATIONS_URL}/{other.id}")
        assert resp.status_code == 404, resp.text

    def test_release_an_unknown_allocation_is_denied(
        self, world, client, user_provider
    ) -> None:
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        resp = client.delete(f"{CONSULTANT_ALLOCATIONS_URL}/alloc-does-not-exist")
        assert resp.status_code == 404, resp.text

    def test_release_requires_the_manage_clients_capability(
        self, world, client, user_provider
    ) -> None:
        _seed_sponsoring_firm(world, mode="SELECTED_CLIENTS", capacity=5)
        allocation = world.manual_processing.seed_allocation("firm-1", "org-a")
        user_provider.set_user(_seed_consultant(world, can_manage_clients=False))
        resp = client.delete(f"{CONSULTANT_ALLOCATIONS_URL}/{allocation.id}")
        assert resp.status_code == 403, resp.text

    def test_allocate_rejects_unknown_payload_fields(
        self, world, client, user_provider
    ) -> None:
        """``extra="forbid"`` — a client can never name a firm/consultant id."""
        self._firm(world, user_provider, mode="SELECTED_CLIENTS", capacity=5)
        resp = client.post(
            CONSULTANT_ALLOCATIONS_URL,
            json={"organization_id": "org-a", "consultant_id": "firm-2"},
        )
        assert resp.status_code == 422, resp.text



