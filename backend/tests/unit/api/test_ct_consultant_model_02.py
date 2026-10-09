"""CT-CONSULTANT-MODEL-IMPLEMENTATION-02 — the ratified PO consultant model.

Findings closed here (``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md``):

* **F-1** — ADMISSION must be capability-gated: the mere existence of an ACTIVE
  ``consultant_clients`` relationship must NOT admit a firm member to a client
  organisation. Admission requires CAP-VIEW-CLIENT (``can_view_client``).
* **F-2** — a consultant had no FINAL-approval capability at all (only
  CarbonTally staff flags existed). PO-6 (B+C) / §13.1 makes final approval
  separable from processing: an ACTIVE engagement **and** CAP-APPROVE
  (``can_approve``) — the blanket customer-owner-only rule does not apply to a
  consultant-managed organisation, and the relationship alone never confers it.
* **F-10** — an administrative capability write must MERGE, never REPLACE: a
  capability absent from the request keeps its stored value, so granting one
  capability cannot silently revoke another.

Everything is asserted server-side against the real routers / real guards over
the in-memory world (``tests.unit.api.conftest``), so an ALLOW is only evidence
when it returns the authorised tenant's own data and a DENY never leaks it
(AGENTS.md §45). ``auth.is_organization_active`` is the D-7 tenant-liveness
predicate and is pinned exactly as ``test_consultant_org_parity`` pins it, so
the decision under test is the capability rule, not store availability.
"""
from __future__ import annotations

import asyncio
import dataclasses
import inspect

import pytest
from fastapi import HTTPException

import auth
from api.consultant_auth import (
    ensure_consultant_approval_authorized,
    ensure_customer_approval_authority,
    resolve_managed_org_ids,
)
from tests.unit.api.fakes import (
    admin_user,
    consultant_user,
    entity_operator_user,
    member_user,
    org_owner_user,
    staff_user,
)

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-1"
CONSULTANT_ID = "u-cons"
COLLEAGUE_ID = "u-second"

ORG_DETAIL = "/api/v3/organizations/{org_id}"
TEAM_PATH = "/api/v3/consultants/me/team"
CAPABILITIES_PATH = "/api/v3/consultants/me/team/{member_id}/capabilities"
CONSULTANT_ME = "/api/v3/consultants/me"


@pytest.fixture
def live_tenants(monkeypatch):
    """Pin the D-7 tenant-liveness predicate to 'all tenants are live'."""
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_consultant(
    world,
    *,
    user_id: str = CONSULTANT_ID,
    can_view_client: bool = True,
    can_approve: bool = False,
    can_manage_team: bool = True,
    role: str = "manager",
    grant_status: str = "active",
    grant_org: str = ORG_A,
):
    """Seed the authoritative consultant identity + its engagement grant.

    ``can_view_client`` defaults True because the helper mirrors an ALREADY
    PROVISIONED member (the state the IMPL-1 backfill produces); the F-1 tests
    pass ``can_view_client=False`` explicitly to exercise denial. ``can_approve``
    is never backfilled, so it is False unless a test grants it.
    """
    world.consultants.seed_profile(FIRM_ID, user_id, "Acme Consultants")
    world.consultants.seed_firm_member(
        FIRM_ID,
        user_id,
        role=role,
        can_view_client=can_view_client,
        can_approve=can_approve,
        can_manage_team=can_manage_team,
    )
    if grant_status is not None:
        world.consultants.seed_client(
            "client-a", FIRM_ID, grant_org, "ACME LTD", status=grant_status
        )
    return consultant_user(user_id, f"{user_id}@example.test")


# ---------------------------------------------------------------------------
# F-1 — capability-gated admission (the relationship alone never admits)
# ---------------------------------------------------------------------------
class TestCapabilityGatedAdmission:
    def test_active_grant_without_the_view_capability_grants_no_scope(
        self, world, client, user_provider, live_tenants
    ):
        """F-1 — ACTIVE relationship + NO CAP-VIEW-CLIENT ⇒ empty scope ⇒ deny."""
        user = _seed_consultant(world, can_view_client=False)
        assert asyncio.run(resolve_managed_org_ids(user, world.bundle())) == ()

        user_provider.set_user(user)
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert ORG_A not in resp.text and "ACME LTD" not in resp.text

    def test_the_view_capability_admits_the_same_active_grant(
        self, world, client, user_provider, live_tenants
    ):
        """F-1 positive control — identical relationship, capability granted."""
        user = _seed_consultant(world, can_view_client=True)
        assert asyncio.run(resolve_managed_org_ids(user, world.bundle())) == (ORG_A,)

        user_provider.set_user(user)
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200

    def test_capability_does_not_override_the_grant_lifecycle(
        self, world, client, user_provider, live_tenants
    ):
        """F-1 — capability is NECESSARY, never SUFFICIENT (D15 preserved).

        CAP-VIEW-CLIENT with a non-active relationship still admits nothing: the
        two admission conditions are independent and both fail closed.
        """
        user = _seed_consultant(world, can_view_client=True, grant_status="ended")
        assert asyncio.run(resolve_managed_org_ids(user, world.bundle())) == ()
        user_provider.set_user(user)
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 403

    def test_revoking_the_capability_takes_effect_on_the_next_request(
        self, world, client, user_provider, live_tenants
    ):
        """F-1 — admission is re-resolved per request; revocation is immediate."""
        user = _seed_consultant(world, can_view_client=True)
        user_provider.set_user(user)
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200

        asyncio.run(
            world.consultants.set_firm_member_capabilities(
                FIRM_ID, f"fm-{CONSULTANT_ID}", {"can_view_client": False}
            )
        )
        resp = client.get(ORG_DETAIL.format(org_id=ORG_A))
        assert resp.status_code == 403
        assert ORG_A not in resp.text

    def test_f1_gate_only_ever_narrows_consultant_admission(
        self, world, client, user_provider, live_tenants
    ):
        """Regression — organisation members are untouched by the F-1 gate."""
        user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@a.test"))
        assert client.get(ORG_DETAIL.format(org_id=ORG_A)).status_code == 200
        assert client.get(ORG_DETAIL.format(org_id=ORG_B)).status_code == 403




# ---------------------------------------------------------------------------
# F-2 — consultant FINAL approval (active engagement AND CAP-APPROVE)
# ---------------------------------------------------------------------------
class TestConsultantFinalApprovalAuthority:
    def test_manager_with_cap_approve_and_active_engagement_approves(
        self, world, live_tenants
    ):
        """PO-6 (B+C) — the consultant-managed organisation's approver."""
        user = _seed_consultant(world, can_approve=True)
        capacity = asyncio.run(
            ensure_customer_approval_authority(
                user, world.bundle(), organization_id=ORG_A
            )
        )
        assert capacity == "consultant"

    def test_active_engagement_without_cap_approve_is_denied(
        self, world, live_tenants
    ):
        """F-2 — the relationship alone never confers final approval (§7.4)."""
        user = _seed_consultant(world, can_approve=False)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    user, world.bundle(), organization_id=ORG_A
                )
            )
        assert exc.value.status_code == 403
        assert "approve" in str(exc.value.detail)

    def test_cap_approve_without_an_active_engagement_is_denied(
        self, world, live_tenants
    ):
        """F-2 — capability without a live grant is denied equally firmly.

        The refusal is the GENERIC organisation-admin detail, not the
        engagement-specific one: a caller who is not admitted to the
        organisation is not told whether an engagement row exists for it. The
        specific "active consultant-client grant required" detail belongs to the
        consultant surface, where the caller's firm context is already admitted
        (``ensure_consultant_approval_authorized``).
        """
        user = _seed_consultant(world, can_approve=True, grant_status="ended")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    user, world.bundle(), organization_id=ORG_A
                )
            )
        assert exc.value.status_code == 403
        assert exc.value.detail == "Organization admin privileges required"
        # ...and the engagement detail IS produced by the consultant-surface gate.
        with pytest.raises(HTTPException) as consultant_exc:
            asyncio.run(
                ensure_consultant_approval_authorized(
                    user, world.bundle(), organization_id=ORG_A
                )
            )
        assert "grant required" in str(consultant_exc.value.detail)

    def test_approval_is_scoped_to_the_engaged_organisation(
        self, world, live_tenants
    ):
        """Cross-client denial — CAP-APPROVE for org-a is not authority over org-b."""
        user = _seed_consultant(world, can_approve=True, grant_org=ORG_A)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    user, world.bundle(), organization_id=ORG_B
                )
            )
        assert exc.value.status_code == 403

    def test_deactivated_member_cannot_approve(self, world, live_tenants):
        """Offboarding revokes the capacity (§11) — membership must be ACTIVE."""
        user = _seed_consultant(world, can_approve=True)
        world.consultants._members[0] = dataclasses.replace(
            world.consultants._members[0], is_active=False
        )
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    user, world.bundle(), organization_id=ORG_A
                )
            )
        assert exc.value.status_code == 403

    def test_org_owner_keeps_the_organisation_capacity(self, world, live_tenants):
        """Regression — D5 organisation approval is unchanged by PO-6."""
        capacity = asyncio.run(
            ensure_customer_approval_authority(
                org_owner_user(ORG_A, "owner-a", "owner@a.test"),
                world.bundle(),
                organization_id=ORG_A,
            )
        )
        assert capacity == "organisation"

    def test_plain_org_member_cannot_give_final_approval(self, world, live_tenants):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    member_user(ORG_A, "member-a", "member@a.test"),
                    world.bundle(),
                    organization_id=ORG_A,
                )
            )
        assert exc.value.status_code == 403

    def test_internal_admin_keeps_the_internal_staff_capacity(
        self, world, live_tenants
    ):
        capacity = asyncio.run(
            ensure_customer_approval_authority(
                admin_user(), world.bundle(), organization_id=ORG_A
            )
        )
        assert capacity == "internal_staff"

    def test_operational_staff_role_gains_no_approval_authority(
        self, world, live_tenants
    ):
        """AGENTS.md §14 — operational staff roles are not administrative ones."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    staff_user("u-staff"), world.bundle(), organization_id=ORG_A
                )
            )
        assert exc.value.status_code == 403

    def test_processing_entity_staff_gains_no_customer_approval(
        self, world, live_tenants
    ):
        """AGENTS.md §12/§45 — the PE boundary is preserved on approval."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    entity_operator_user("entity-1"),
                    world.bundle(),
                    organization_id=ORG_A,
                )
            )
        assert exc.value.status_code == 403

    def test_non_consultant_is_denied_with_the_standard_detail(
        self, world, live_tenants
    ):
        """An unknown caller learns nothing new (same detail as before F-2)."""
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                ensure_customer_approval_authority(
                    consultant_user("u-nobody", "nobody@example.test"),
                    world.bundle(),
                    organization_id=ORG_A,
                )
            )
        assert exc.value.status_code == 403
        assert exc.value.detail == "Organization admin privileges required"


# ---------------------------------------------------------------------------
# F-10 — capability administration MERGES, never REPLACES
# ---------------------------------------------------------------------------
class TestCapabilityAdministrationMerge:
    def test_granting_one_capability_preserves_every_other(
        self, world, client, user_provider
    ):
        """F-10 — the write is a MERGE: stored flags absent from the body survive."""
        leader = _seed_consultant(world, can_approve=False)
        world.consultants.seed_firm_member(
            FIRM_ID,
            COLLEAGUE_ID,
            role="consultant",
            can_view_client=True,
            can_manage_team=True,
        )
        user_provider.set_user(leader)

        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
            json={"can_approve": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["changed"] == {"can_approve": True}
        assert body["member"]["can_approve"] is True
        # The untouched capabilities are still exactly what they were.
        assert body["member"]["can_view_client"] is True

        member = asyncio.run(
            world.consultants.get_firm_member(FIRM_ID, f"fm-{COLLEAGUE_ID}")
        )
        assert member.can_manage_team is True
        assert member.can_upload_documents is False

    def test_revoking_one_capability_preserves_the_granted_one(
        self, world, client, user_provider
    ):
        """F-10 — revoking CAP-VIEW-CLIENT does not silently drop CAP-APPROVE."""
        leader = _seed_consultant(world, can_approve=False)
        world.consultants.seed_firm_member(
            FIRM_ID, COLLEAGUE_ID, role="consultant", can_approve=True
        )
        user_provider.set_user(leader)

        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
            json={"can_view_client": False},
        )
        assert resp.status_code == 200
        assert resp.json()["member"]["can_approve"] is True

    def test_the_roster_reports_both_capabilities(
        self, world, client, user_provider
    ):
        """The firm can see what it administers (grant/revoke control needs it)."""
        user = _seed_consultant(world, can_approve=True)
        user_provider.set_user(user)
        resp = client.get(TEAM_PATH)
        assert resp.status_code == 200
        row = next(
            m for m in resp.json()["members"] if m["user_id"] == CONSULTANT_ID
        )
        assert row["can_view_client"] is True
        assert row["can_approve"] is True

    def test_a_member_cannot_change_their_own_capabilities(
        self, world, client, user_provider
    ):
        """No silent self-escalation to CAP-APPROVE."""
        user = _seed_consultant(world, can_approve=False)
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{CONSULTANT_ID}"),
            json={"can_approve": True},
        )
        assert resp.status_code == 422
        member = asyncio.run(
            world.consultants.get_firm_member(FIRM_ID, f"fm-{CONSULTANT_ID}")
        )
        assert member.can_approve is False

    def test_capability_write_requires_the_manage_team_capability(
        self, world, client, user_provider
    ):
        user = _seed_consultant(world, can_manage_team=False)
        world.consultants.seed_firm_member(FIRM_ID, COLLEAGUE_ID, role="consultant")
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
            json={"can_approve": True},
        )
        assert resp.status_code == 403

    def test_another_firms_member_is_not_addressable(
        self, world, client, user_provider
    ):
        """Firm scoping — a foreign member id is not found, not modified."""
        user = _seed_consultant(world)
        world.consultants.seed_profile("firm-2", "u-other", "Other Consultants")
        world.consultants.seed_firm_member(
            "firm-2", "u-other", role="consultant", can_approve=False
        )
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id="fm-u-other"),
            json={"can_approve": True},
        )
        assert resp.status_code == 404
        member = asyncio.run(
            world.consultants.get_firm_member("firm-2", "fm-u-other")
        )
        assert member.can_approve is False

    def test_unknown_capability_names_cannot_be_written(
        self, world, client, user_provider
    ):
        """A forged/unknown field is rejected, not granted.

        CT03 NOTE (supersession): this test originally used ``can_manage_team``
        as its "forged" field, because CT02's model addressable only the two new
        capabilities. CT03 (P5 — "surface other existing operational
        capabilities") deliberately makes the pre-existing firm capabilities
        (``can_manage_team`` et al.) administrable through the SAME endpoint, so
        ``can_manage_team`` is no longer unknown. The F-10 property under test is
        unchanged and is now asserted with a genuinely unknown name (and an
        attempted COMMERCIAL ENTITLEMENT, which must never be addressable — P5).
        """
        user = _seed_consultant(world)
        world.consultants.seed_firm_member(FIRM_ID, COLLEAGUE_ID, role="consultant")
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
            json={"can_grant_seat_entitlement": True},
        )
        assert resp.status_code == 422
        member = asyncio.run(
            world.consultants.get_firm_member(FIRM_ID, f"fm-{COLLEAGUE_ID}")
        )
        assert member.can_manage_team is False

    @pytest.mark.parametrize("body", [{}, {"can_approve": None}])
    def test_empty_or_null_payload_is_rejected(
        self, world, client, user_provider, body
    ):
        user = _seed_consultant(world)
        world.consultants.seed_firm_member(FIRM_ID, COLLEAGUE_ID, role="consultant")
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"), json=body
        )
        assert resp.status_code == 422

    def test_repository_rejects_a_non_capability_column(self, world, live_tenants):
        """F-10 — the write is restricted to the capability allow-list."""
        _seed_consultant(world)
        with pytest.raises(ValueError):
            asyncio.run(
                world.consultants.set_firm_member_capabilities(
                    FIRM_ID, f"fm-{CONSULTANT_ID}", {"is_active": False}
                )
            )


# ---------------------------------------------------------------------------
# Cross-cutting — the surfaces expose / consume the two capabilities
# ---------------------------------------------------------------------------
class TestCapabilityWiring:
    def test_me_exposes_the_two_capabilities(self, world, client, user_provider):
        """The UI can only gate the approve control from the server's own flags."""
        user = _seed_consultant(world, can_view_client=True, can_approve=True)
        user_provider.set_user(user)
        resp = client.get(CONSULTANT_ME)
        assert resp.status_code == 200
        body = resp.json()
        assert body["can_view_client"] is True
        assert body["can_approve"] is True

    def test_customer_review_route_uses_the_shared_approval_helper(self):
        """F-2 wiring — the FINAL-approval gate is the shared authority helper.

        It cannot be a route-level ``require_org_admin`` dependency: the authority
        depends on the item's SERVER-DERIVED organisation, which only exists once
        the resource has been loaded.
        """
        from api.v3_processing_workflow import customer_review_item

        source = inspect.getsource(customer_review_item)
        assert "ensure_customer_approval_authority" in source
        assert "batch.organization_id" in source
        assert "require_org_admin" not in source
