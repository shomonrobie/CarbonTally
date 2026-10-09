"""CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01 — consultant organisation parity.

Ratified design under test (PD-1/PD-3/PD-4/PD-5/PD-6/PD-7/PD-12):

    A consultant managing a client organisation reaches the SAME CarbonTally
    Organisation product surface a customer uses — same routes, same contract,
    same authorisation guard family — rather than a reduced consultant
    mini-dashboard. The consultant is admitted by the AUTHORIZATION layer
    (``require_org_member()`` → ``resolve_managed_org_ids`` → ``ensure_org_access``
    / ``enforce_org_path_scope``), NOT by inventing an ``organization_members``
    row (PD-12). The organisation scope is resolved server-side from ACTIVE
    ``consultant_clients`` grants and never from client-supplied input.

The tests drive the REAL routers over the in-memory world (``tests.unit.api.
conftest``), so they assert the real HTTP decision plus the TARGET RESOURCE: a
denial must never return the other tenant's data, and an ALLOW must return the
managed client's own data (AGENTS.md §45 — every unexpected ALLOW is a finding,
and a 200 is only evidence when the payload belongs to the authorised tenant).

``auth.is_organization_active`` is the D-7 tenant-liveness predicate, which
fails closed against the service-role store; unit tests therefore pin it
explicitly (exactly as ``test_f05_r1_org_scope_authorization`` pins the store)
so the decision under test is the organisation-scope rule, not store
availability.
"""
from __future__ import annotations

import asyncio
import dataclasses

import pytest
from fastapi import HTTPException

import auth
from api.dependencies import ensure_org_access, get_repositories
from auth import ORGANIZATION_SUSPENDED_DETAIL, require_org_member_or_internal_staff
from tests.unit.api.fakes import (
    consultant_user,
    entity_operator_user,
    member_user,
    org_owner_user,
    staff_user,
)

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-c1"
CONSULTANT_ID = "u-c1"

#: The shared Organisation surface a customer uses (``api/v3_organizations.py``).
ORG_DETAIL = "/api/v3/organizations/{org_id}"
ORG_METADATA = "/api/v3/organizations/{org_id}/metadata"
ORG_PROFILE = "/api/v3/organizations/{org_id}/profile"
ORG_MEMBERS = "/api/v3/organizations/{org_id}/members"
BILLING_OVERVIEW = "/api/v3/billing/me"


@pytest.fixture
def live_tenants(monkeypatch):
    """Pin the D-7 tenant-liveness predicate to 'all tenants are live'.

    Two bindings exist: the guard family in ``auth.py`` (path-scope decisions)
    and the re-exported name in ``api/dependencies.py`` (``ensure_org_access``,
    which decides query/body-named organisations).
    """
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


@pytest.fixture
def suspended_tenants(monkeypatch):
    """Pin the D-7 tenant-liveness predicate to 'every tenant is suspended'."""
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: False)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: False
    )


def _seed_consultant(
    world,
    *,
    user_id: str = CONSULTANT_ID,
    firm_id: str = FIRM_ID,
    grants=(("cc-a", ORG_A, "active"),),
    member_active: bool = True,
    firm_active: bool = True,
    role: str = "owner",
    can_view_client: bool = True,
):
    """Seed an authoritative consultant principal + its client grants.

    Mirrors the real data shape: ``consultant_profiles`` (the firm) →
    ``consultant_firm_members`` (the authenticated user) → ``consultant_clients``
    (the per-client grant whose ``status`` is the only thing that grants access).

    ``can_view_client`` is the F-1/§7.4 ADMISSION capability: without it the
    member's reachable organisation scope is EMPTY (``resolve_managed_org_ids``),
    so every organisation-plane route denies however healthy the grant looks.
    """
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=firm_active)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role=role,
        is_active=member_active,
        can_manage_clients=True,
        can_upload_documents=True,
        can_generate_reports=True,
        can_view_client=can_view_client,
    )
    for client_id, org_id, status in grants:
        world.consultants.seed_client(
            client_id, firm_id, org_id, f"Client {org_id}", status=status
        )
    return consultant_user(user_id, f"{user_id}@example.test")


def _grant_status(world, client_id: str, status: str) -> None:
    """Mutate an existing grant's lifecycle state (revocation / suspension).

    ``ConsultantClient`` rows are frozen, so the grant is replaced the way the
    production repository replaces a row on a lifecycle transition.
    """
    for index, client in enumerate(world.consultants._clients):
        if client.id == client_id:
            world.consultants._clients[index] = dataclasses.replace(
                client, status=status
            )
            return
    raise AssertionError(f"no seeded client {client_id!r}")


# ---------------------------------------------------------------------------
# AC-01 / AC-02 — the same Organisation surface, permitted and forbidden
# ---------------------------------------------------------------------------
class TestConsultantReachesManagedClientOrganisation:
    def test_consultant_with_active_grant_gets_the_same_organisation_payload(
        self, world, client, user_provider, live_tenants
    ):
        """AC-01 — parity is proven by comparing against the CUSTOMER's own read.

        The consultant-managed client must reach the identical route and receive
        the identical payload an organisation owner of that client receives; a
        "consultant view" that merely returns 200 with different (or reduced)
        data would not be parity.
        """
        user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@a.test"))
        customer_response = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert customer_response.status_code == 200

        user_provider.set_user(_seed_consultant(world))
        consultant_response = client.get(ORG_DETAIL.format(org_id=ORG_A))

        assert consultant_response.status_code == 200
        assert consultant_response.json() == customer_response.json()
        assert consultant_response.json()["organization"]["id"] == ORG_A
        assert consultant_response.json()["organization"]["name"] == "Org A"

    def test_consultant_with_active_grant_reads_client_metadata(
        self, world, client, user_provider, live_tenants
    ):
        """AC-01 — the client's own metadata payload, byte-for-byte the customer's."""
        user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@a.test"))
        customer_metadata = client.get(ORG_METADATA.format(org_id=ORG_A))

        user_provider.set_user(_seed_consultant(world))
        resp = client.get(ORG_METADATA.format(org_id=ORG_A))

        assert resp.status_code == 200
        assert resp.json() == customer_metadata.json()
        assert resp.json()["metadata"]["organization_id"] == ORG_A

    def test_consultant_is_denied_a_non_granted_organisation(
        self, world, client, user_provider, live_tenants
    ):
        """AC-02/AC-12 — path forgery carries no authority and leaks nothing."""
        user_provider.set_user(_seed_consultant(world))
        resp = client.get(ORG_DETAIL.format(org_id=ORG_B))
        assert resp.status_code == 403
        # Target-resource isolation: the denial must not carry org-b's data.
        assert "Org B" not in resp.text
        assert ORG_B not in resp.text

    def test_consultant_is_denied_a_non_granted_organisation_across_read_routes(
        self, world, client, user_provider, live_tenants
    ):
        """AC-02 — the rule is central, not one endpoint's local check."""
        user_provider.set_user(_seed_consultant(world))
        for route in (ORG_DETAIL, ORG_METADATA, ORG_MEMBERS):
            resp = client.get(route.format(org_id=ORG_B))
            assert resp.status_code == 403, route
            assert "Org B" not in resp.text

    def test_consultant_reaches_only_its_own_granted_client(
        self, world, client, user_provider, live_tenants
    ):
        """AC-02 — the granted client passes, every other tenant is denied."""
        user_provider.set_user(
            _seed_consultant(world, grants=(("cc-a", ORG_A, "active"),))
        )
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200
        assert client.get(ORG_DETAIL.format(org_id=ORG_B)).status_code == 403


# ---------------------------------------------------------------------------
# AC-03 / AC-04 / AC-05 — grant lifecycle, firm membership, live re-resolution
# ---------------------------------------------------------------------------
class TestGrantLifecycle:
    @pytest.mark.parametrize(
        "status", ["pending", "rejected", "suspended", "ended", "inactive"]
    )
    def test_non_active_grant_grants_nothing(
        self, world, client, user_provider, live_tenants, status
    ):
        """D15 — only ``status='active'`` grants organisation access."""
        user_provider.set_user(
            _seed_consultant(world, grants=(("cc-a", ORG_A, status),))
        )
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Org A" not in resp.text

    def test_consultant_with_no_grants_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        """An admitted consultant principal with an empty grant set is denied."""
        user_provider.set_user(_seed_consultant(world, grants=()))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 403

    def test_inactive_firm_membership_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        """AC-04 — revoked firm membership resolves to no consultant at all."""
        user_provider.set_user(_seed_consultant(world, member_active=False))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 403

    def test_inactive_firm_profile_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        """AC-04 — an inactive consultant firm grants none of its clients."""
        user_provider.set_user(_seed_consultant(world, firm_active=False))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 403

    def test_revoking_the_grant_takes_effect_on_the_next_request(
        self, world, client, user_provider, live_tenants
    ):
        """AC-05 — scope is re-resolved per request (no cached authority)."""
        user_provider.set_user(_seed_consultant(world))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200
        _grant_status(world, "cc-a", "ended")
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Org A" not in resp.text

    def test_suspended_client_tenant_denies_the_consultant(
        self, world, client, user_provider, suspended_tenants
    ):
        """D-7 Decision B — a suspended client tenant grants its consultant nothing."""
        user_provider.set_user(_seed_consultant(world))
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Org A" not in resp.text


# ---------------------------------------------------------------------------
# AC-18 / AC-19 — every pre-existing boundary is unchanged
# ---------------------------------------------------------------------------
class TestExistingBoundariesUnchanged:
    def test_org_member_is_still_confined_to_its_own_organisation(
        self, world, client, user_provider, live_tenants
    ):
        """AC-18 — a plain member of org-a still cannot read org-b."""
        user_provider.set_user(member_user(ORG_A, "member-a", "m@a.test"))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200
        assert client.get(ORG_DETAIL.format(org_id=ORG_B)).status_code == 403

    def test_non_consultant_without_membership_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        """AC-19 — a principal with no membership and no grant stays denied.

        ``managed_org_ids is None`` (not a consultant context) must preserve the
        historical denial exactly; the consultant branch must not become a
        generic "no organisation = try harder" path.
        """
        user_provider.set_user(consultant_user("u-nobody", "nobody@example.test"))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 403

    def test_processing_entity_staff_cannot_reach_customer_organisations(
        self, world, client, user_provider, live_tenants
    ):
        """D20 scope-first — PE staff never gain customer-organisation access."""
        user_provider.set_user(entity_operator_user("entity-1"))
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Org A" not in resp.text

    def test_internal_staff_decision_is_unchanged_on_the_member_guard(
        self, world, client, user_provider, live_tenants
    ):
        """The plain member guard never admitted internal staff — unchanged.

        ``require_org_member()`` is a MEMBERSHIP guard; CarbonTally INTERNAL staff
        are served by the staff-aware variant instead (G2). The consultant
        admission added for PD-3 must not alter that branch, so a staff principal
        is still refused with the historical status and message.
        """
        user_provider.set_user(staff_user("u-staff"))
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Organization member access required" in resp.text

    def test_internal_staff_still_pass_the_member_or_staff_guard(self, world):
        """G2 — the internal-staff operational exemption itself is intact."""
        checker = require_org_member_or_internal_staff()
        user = staff_user("u-staff")
        assert asyncio.run(checker(current_user=user, request=None)) is user

    def test_consultant_is_not_admitted_by_the_legacy_document_guard(self, world):
        """PD-1 scope — parity covers the V3 Organisation surface, not legacy guards.

        ``require_org_member_or_internal_staff()`` protects the legacy
        ``/api/documents/*`` activity/review routes, whose handlers go on to
        re-check RECORD-level membership through the service-role client. A
        consultant holds no membership, so admitting the principal there would
        grant nothing while making the denial surface less clear. The V3
        consultant workspace uses ``/api/v3/*`` (already parity-enabled), so the
        legacy guard is deliberately left unchanged — a denial, never a leak.
        """
        checker = require_org_member_or_internal_staff()
        user = consultant_user(CONSULTANT_ID, "u-c1@example.test")
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(checker(current_user=user, request=None))
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Organization member access required"

    def test_unauthenticated_call_is_401(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_unauthenticated()
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 401


# ---------------------------------------------------------------------------
# PD-4 / PD-5 / PD-6 / PD-12 — what a consultant still must NOT reach
# ---------------------------------------------------------------------------
class TestConsultantDoesNotGainOwnerAuthority:
    def test_consultant_cannot_use_owner_admin_only_routes(
        self, world, client, user_provider, live_tenants
    ):
        """PD-4/PD-5 — ``require_org_admin`` authority is role-based.

        A consultant holds NO organisation role, so ownership/administration
        (profile writes, membership, invitations, engagements) stays denied even
        for a client it legitimately manages. Parity is the OPERATING surface,
        not the customer's administrative authority.
        """
        user_provider.set_user(_seed_consultant(world))
        resp = client.put(
            ORG_PROFILE.format(org_id=ORG_A),
            json={"name": "Renamed by consultant"},
        )
        assert resp.status_code == 403
        assert "Organization admin privileges required" in resp.text

    def test_managed_client_billing_is_not_exposed_to_the_consultant(
        self, world, client, user_provider, live_tenants
    ):
        """PD-6 — CarbonTally bills consultant FIRMS, not their managed clients.

        The billing surface resolves its organisation from the CALLER
        (``_resolve_org(current_user)``) and declares no organisation path
        parameter, so a consultant — who owns no organisation — can never read a
        managed client's billing. That is a server-side fact, not a hidden
        navigation link.
        """
        user_provider.set_user(_seed_consultant(world))
        resp = client.get(BILLING_OVERVIEW)
        assert resp.status_code != 200
        assert resp.status_code in (401, 403, 404, 422)

    def test_consultant_principal_is_not_an_organisation_member(
        self, world, client, user_provider, live_tenants
    ):
        """PD-12 — admission is by authorization, not by inventing membership.

        The parity surface must be reached while the principal is still NOT an
        ``organization_members`` row: no membership inheritance, no role, no
        ``organization_id`` binding.
        """
        user = _seed_consultant(world)
        user_provider.set_user(user)
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200
        assert user.is_org_member is False
        assert user.organization_id is None

    def test_guard_fails_closed_without_the_consultant_repository(
        self, world, app, client, user_provider, live_tenants
    ):
        """An unusable repository must deny, never become an implicit allow."""
        bundle = world.bundle()
        bundle.consultants = None
        app.dependency_overrides[get_repositories] = lambda: bundle
        user_provider.set_user(_seed_consultant(world))
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert "Org A" not in resp.text


# ---------------------------------------------------------------------------
# Query/body-named organisations — the second half of the organisation scope
# ---------------------------------------------------------------------------
class TestOrganisationNamedOutsideThePath:
    """``/api/v3/emissions/dashboard?organization_id=...`` style surfaces.

    These routes declare no organisation path parameter, so
    ``enforce_org_path_scope`` is deliberately a no-op and ``ensure_org_access``
    is the single decision point. Consultant parity must therefore be complete
    there too — including the D-7 suspended-tenant rule.
    """

    @staticmethod
    def _principal(managed):
        user = consultant_user(CONSULTANT_ID, "u-c1@example.test")
        user.managed_org_ids = list(managed)
        return user

    def test_granted_organisation_is_allowed(self, live_tenants):
        ensure_org_access(self._principal([ORG_A]), ORG_A)

    def test_organisation_outside_the_grant_set_is_denied(self, live_tenants):
        with pytest.raises(HTTPException) as excinfo:
            ensure_org_access(self._principal([ORG_A]), ORG_B)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Organization access denied"

    def test_empty_grant_set_is_denied(self, live_tenants):
        with pytest.raises(HTTPException) as excinfo:
            ensure_org_access(self._principal([]), ORG_A)
        assert excinfo.value.status_code == 403

    def test_suspended_client_tenant_is_denied(self, suspended_tenants):
        """D-7 Decision B applies wherever the organisation is named."""
        with pytest.raises(HTTPException) as excinfo:
            ensure_org_access(self._principal([ORG_A]), ORG_A)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == ORGANIZATION_SUSPENDED_DETAIL

    def test_principal_without_membership_or_grant_is_denied(self, live_tenants):
        user = consultant_user("u-nobody", "nobody@example.test")
        with pytest.raises(HTTPException) as excinfo:
            ensure_org_access(user, ORG_A)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Organization access denied"


# ---------------------------------------------------------------------------
# F-NAV-1 — the D30 reporting read surface is the SAME organisation plane
# ---------------------------------------------------------------------------
#: The three customer-plane reporting reads the client workspace calls when a
#: consultant operates a managed client (``frontend/src/v3/api.js``:
#: ``getCustomerDashboard`` / ``getEmissionsTrend`` / ``getMemberActivity``).
REPORTING_ROUTES = (
    "/api/v3/reporting/customer-dashboard?organization_id={org}",
    "/api/v3/reporting/emissions-trend?organization_id={org}&months=12",
    "/api/v3/reporting/member-activity?organization_id={org}",
)


def _seed_reported_aggregates(world) -> None:
    """Populate the D30 aggregate fakes with the CLIENT tenant's own numbers."""
    world.reporting.emissions_summary_result = {
        "total_kg": 183.0, "row_count": 1,
        "by_scope": [{"scope": "Scope 1", "kg": 183.0, "rows": 1}],
        "by_month": [{"month": "2025-06", "kg": 183.0, "rows": 1}],
    }
    world.reporting.document_summary_result = {
        "total_documents": 4, "processing_by_status": {"completed": 2, "pending": 2},
        "processed": 2, "pending": 2, "requiring_attention": 1,
    }
    world.reporting.processing_summary_result = {
        "batches": {"total": 2, "by_status": {"open": 2}},
        "items": {"total": 4, "by_stage": {"source": 1, "approval": 3},
                  "mapped": 3, "unmapped": 1, "complete_pct": 75.0},
    }
    world.reporting.issues_summary_result = {
        "by_status": {"open": 1}, "open": 1, "sla_breached_open": 0,
    }
    world.reporting.report_summary_result = {"completed": 1, "pending": 1}
    world.reporting.emissions_trend_result = {
        "organization_id": ORG_A,
        "months": [{"month": "2025-06", "kg": 183.0, "rows": 1}],
    }
    world.reporting.member_activity_result = [
        {"user_id": "member-a", "name": "A Member", "documents_uploaded": 2,
         "issues_created": 1, "issues_resolved": 0, "extraction_batches": 1,
         "emissions_rows": 0},
    ]


class TestConsultantReachesManagedClientReporting:
    """F-NAV-1 — an ACTIVE-grant consultant reads its client's reporting plane.

    These three routes declare no organisation PATH parameter, so
    ``enforce_org_path_scope`` is deliberately a no-op and the guard chain was
    ``get_current_user`` + ``ensure_org_access`` — which refuses a consultant
    (not an ``organization_members`` row, PD-12) before the consultant-aware
    admission of ``require_org_member()`` is ever reached. A consultant
    operating its OWN managed client therefore received 403 inside the client
    workspace (recorded verbatim in CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A
    §19). They now run the SAME guard family as the emissions/reports surfaces,
    so parity is complete here too — and every pre-existing boundary (member,
    cross-org, PE staff, suspension, revocation, anonymity) is unchanged.
    """

    def test_consultant_with_active_grant_gets_the_same_reporting_payloads(
        self, world, client, user_provider, live_tenants
    ):
        """F-NAV-1 — parity proven by comparing against the CUSTOMER's own read."""
        _seed_reported_aggregates(world)
        user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@a.test"))
        customer = {
            route: client.get(route.format(org=ORG_A)) for route in REPORTING_ROUTES
        }
        for route, response in customer.items():
            assert response.status_code == 200, route

        user_provider.set_user(_seed_consultant(world))
        for route in REPORTING_ROUTES:
            resp = client.get(route.format(org=ORG_A))
            assert resp.status_code == 200, route
            assert resp.json() == customer[route].json(), route
            # A 200 is only evidence when the payload is the AUTHORISED tenant's.
            assert resp.json()["organization_id"] == ORG_A, route

    def test_consultant_is_denied_reporting_for_a_non_granted_organisation(
        self, world, client, user_provider, live_tenants
    ):
        """No cross-tenant read, and no target-resource leakage in the denial."""
        _seed_reported_aggregates(world)
        user_provider.set_user(_seed_consultant(world))
        for route in REPORTING_ROUTES:
            resp = client.get(route.format(org=ORG_B))
            assert resp.status_code == 403, route
            assert ORG_B not in resp.text, route
            # The uniform guard denial: it must not become a consultant-specific
            # message that discloses whether org-b exists or is granted.
            assert (
                resp.json()["error"]["message"] == "Organization access denied"
            ), route

    def test_reporting_denies_a_consultant_without_the_admission_capability(
        self, world, client, user_provider, live_tenants
    ):
        """F-1/§7.4 — CAP-VIEW-CLIENT admits; the relationship row alone does not."""
        _seed_reported_aggregates(world)
        user_provider.set_user(_seed_consultant(world, can_view_client=False))
        for route in REPORTING_ROUTES:
            assert client.get(route.format(org=ORG_A)).status_code == 403, route

    def test_revoking_the_grant_closes_the_reporting_plane(
        self, world, client, user_provider, live_tenants
    ):
        """AC-05 — scope is re-resolved per request on the reporting routes too."""
        _seed_reported_aggregates(world)
        user_provider.set_user(_seed_consultant(world))
        assert client.get(REPORTING_ROUTES[0].format(org=ORG_A)).status_code == 200
        _grant_status(world, "cc-a", "ended")
        for route in REPORTING_ROUTES:
            resp = client.get(route.format(org=ORG_A))
            assert resp.status_code == 403, route
            assert ORG_A not in resp.text, route

    def test_suspended_client_tenant_closes_the_reporting_plane(
        self, world, client, user_provider, suspended_tenants
    ):
        """D-7 Decision B — a suspended client tenant serves its consultant nothing."""
        _seed_reported_aggregates(world)
        user_provider.set_user(_seed_consultant(world))
        for route in REPORTING_ROUTES:
            resp = client.get(route.format(org=ORG_A))
            assert resp.status_code == 403, route
            assert ORG_A not in resp.text, route
            # ``api/router.py`` renders denials in the standard envelope
            # (``{"error": {"code", "message", "details"}}``), so the reason is
            # assertable without leaking the tenant.
            assert (
                resp.json()["error"]["message"] == ORGANIZATION_SUSPENDED_DETAIL
            ), route

    def test_processing_entity_staff_cannot_reach_client_reporting(
        self, world, client, user_provider, live_tenants
    ):
        """D20 scope-first — the reporting plane never becomes a PE surface."""
        user_provider.set_user(entity_operator_user("entity-1"))
        for route in REPORTING_ROUTES:
            resp = client.get(route.format(org=ORG_A))
            assert resp.status_code == 403, route
            assert ORG_A not in resp.text, route

    def test_reporting_still_requires_authentication(self, client, user_provider):
        """The guard swap must not open an anonymous path to tenant reporting."""
        user_provider.set_unauthenticated()
        for route in REPORTING_ROUTES:
            assert client.get(route.format(org=ORG_A)).status_code == 401, route

    def test_direct_customer_reporting_decision_is_unchanged(
        self, world, client, user_provider, live_tenants
    ):
        """AC-18 — the customer path on these routes is untouched by the fix."""
        _seed_reported_aggregates(world)
        user_provider.set_user(member_user(ORG_A, "member-a", "m@a.test"))
        for route in REPORTING_ROUTES:
            assert client.get(route.format(org=ORG_A)).status_code == 200, route
            resp = client.get(route.format(org=ORG_B))
            assert resp.status_code == 403, route
            assert ORG_B not in resp.text, route




