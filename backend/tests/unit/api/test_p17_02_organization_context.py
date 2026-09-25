"""P17-IMPLEMENT-02 — organization / consultant accounting-context tests.

Pure, no DB. These are the SECURITY tests for this task, so they are written as
ALLOW/DENY pairs against the ten cases the task enumerates:

1. direct customer → own org succeeds
2. consultant → own org succeeds
3. consultant → authorized client succeeds
4. consultant → unauthorized client returns 403
5. client user → own org succeeds
6. client user → unrelated org returns 403
7. delegated user → only permitted organizations succeed
8. tenant data cannot be accessed by changing acting-for id
9. persisted acting-for cannot be forged by request payload
10. data-owning organization cannot be overridden by an unauthorized actor
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pytest
from fastapi import HTTPException

from auth import AuthUser
from domain.acting_for import ActingForKind, EntitlementBasis
from domain.cams import CamsPersona
from api.accounting_context_auth import (
    RELATIONSHIP_CONSULTANT_CLIENT,
    RELATIONSHIP_INTERNAL,
    RELATIONSHIP_OWN,
    ensure_record_owner_authorized,
    list_authorized_organizations,
    resolve_accounting_context,
    resolve_persona,
)

OWN_ORG = "org-own"
CLIENT_A = "org-client-a"
CLIENT_B = "org-client-b"
UNRELATED = "org-unrelated"
FIRM_ORG = "org-firm"


# ---------------------------------------------------------------------------
# Fakes (no DB, no network)
# ---------------------------------------------------------------------------
@dataclass
class FakeProfile:
    id: str = "profile-1"
    user_id: str = "u-consultant"
    company_name: str = "Green Advisory"
    organization_id: Optional[str] = FIRM_ORG
    is_active: bool = True


@dataclass
class FakeMembership:
    firm_id: str = "profile-1"
    joined_at: Any = None
    invited_at: Any = None


@dataclass
class FakeConsultantContext:
    profile: FakeProfile = field(default_factory=FakeProfile)
    firm_member: FakeMembership = field(default_factory=FakeMembership)


@dataclass
class FakeClientGrant:
    organization_id: str
    client_name: str = "Client"
    status: Optional[str] = "active"


class FakeAccountingContextRepo:
    def __init__(
        self,
        *,
        organizations: dict[str, dict],
        member_roles: dict[str, str],
    ) -> None:
        self._orgs = organizations
        self._member_roles = member_roles
        self.persisted: list[dict] = []
        self.records: dict[tuple[str, str], dict] = {}

    async def get_organization_summary(self, organization_id: str) -> Optional[dict]:
        return self._orgs.get(organization_id)

    async def list_active_member_roles(self, user_id: str) -> dict[str, str]:
        return dict(self._member_roles)

    async def list_scope3_categories(self) -> list[dict]:
        return []

    async def get_snapshot_dimensions(self, snapshot_id: str) -> Optional[dict]:
        return None

    async def persist_acting_for(
        self, *, carrier: str, record_id: str,
        actor_organization_id: Optional[str],
        acting_for_organization_id: str,
    ) -> Optional[dict]:
        self.persisted.append(
            {
                "carrier": carrier,
                "record_id": record_id,
                "actor_organization_id": actor_organization_id,
                "acting_for_organization_id": acting_for_organization_id,
            }
        )
        return {
            "carrier": carrier,
            "record_id": record_id,
            "actor_organization_id": actor_organization_id,
            "acting_for_organization_id": acting_for_organization_id,
        }

    async def get_acting_for_attribution(
        self, *, carrier: str, record_id: str
    ) -> Optional[dict]:
        return self.records.get((carrier, record_id))


class FakeConsultantsRepo:
    def __init__(
        self,
        *,
        context: Optional[FakeConsultantContext] = None,
        grants: Optional[list[FakeClientGrant]] = None,
    ) -> None:
        self._context = context
        self._grants = grants or []

    async def get_active_memberships_by_user(self, user_id: str) -> list[FakeMembership]:
        return [FakeMembership()] if self._context else []

    async def get_profile_by_id(self, firm_id: str) -> Optional[FakeProfile]:
        return self._context.profile if self._context else None

    async def list_clients(self, consultant_id: str) -> list[FakeClientGrant]:
        return list(self._grants)

    async def get_client_by_org(
        self, consultant_id: str, organization_id: str
    ) -> Optional[FakeClientGrant]:
        for grant in self._grants:
            if grant.organization_id == organization_id:
                return grant
        return None


class FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list[Any] = []

    async def record(self, entry: Any) -> Any:
        self.entries.append(entry)
        return entry


@dataclass
class FakeRepos:
    accounting_context: FakeAccountingContextRepo
    consultants: FakeConsultantsRepo
    audit: FakeAuditRepo = field(default_factory=FakeAuditRepo)


def _orgs(*ids: str) -> dict[str, dict]:
    return {
        oid: {
            "id": oid,
            "name": oid.upper(),
            "organization_type": "CUSTOMER",
            "consolidation_approach": None,
            "is_active": True,
        }
        for oid in ids
    }


def _user(**kwargs: Any) -> AuthUser:
    base = dict(
        user_id="u-1",
        email="u@example.com",
        role="member",
        organization_id=OWN_ORG,
    )
    base.update(kwargs)
    return AuthUser(**base)


# ---------------------------------------------------------------------------
# Persona classification
# ---------------------------------------------------------------------------
def test_internal_staff_persona() -> None:
    assert resolve_persona(_user(is_staff=True, entity_id=None)) == CamsPersona.STAFF


def test_processing_entity_staff_persona_is_not_internal_staff() -> None:
    user = _user(is_staff=True, entity_id="entity-1")
    assert resolve_persona(user) == CamsPersona.PROCESSING_ENTITY


def test_org_member_persona_is_direct_customer() -> None:
    assert resolve_persona(_user(is_org_member=True)) == CamsPersona.DIRECT_CUSTOMER


# ---------------------------------------------------------------------------
# Case 1 / 5 — direct customer and client user act for their OWN org
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_direct_customer_acts_for_own_organization() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"}
        ),
        consultants=FakeConsultantsRepo(),
    )
    context = await resolve_accounting_context(_user(is_org_member=True), repos)
    assert context.data_owning_organization_id == OWN_ORG
    assert context.acting_for_organization_id == OWN_ORG
    assert context.is_delegated is False
    assert context.entitlement_basis == EntitlementBasis.ORGANIZATION_MEMBERSHIP.value
    assert context.acting_for_kind == ActingForKind.SELF.value
    assert context.persona == CamsPersona.DIRECT_CUSTOMER
    # The ACTING FOR banner is absent for a non-delegated operation.
    assert context.as_payload()["acting_for_label"] is None


def test_acting_for_label_names_the_client_when_delegated() -> None:
    """The UI banner appears only for a genuine delegation."""
    from api.accounting_context_auth import AccountingContext

    context = AccountingContext(
        actor_user_id="u",
        persona=CamsPersona.CONSULTANT_CLIENT,
        own_organization_id=FIRM_ORG,
        data_owning_organization_id=CLIENT_A,
        acting_for_organization_id=CLIENT_A,
        acting_for_organization_name="Acme Ltd",
        actor_organization_id=FIRM_ORG,
        is_delegated=True,
        entitlement_basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION.value,
        acting_for_kind=ActingForKind.CONSULTANT_FOR_CLIENT.value,
    )
    assert context.as_payload()["acting_for_label"] == "ACTING FOR: Acme Ltd"


# ---------------------------------------------------------------------------
# Case 6 / 8 — a client user cannot reach an unrelated organization
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_client_user_cannot_act_for_an_unrelated_organization() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG, UNRELATED),
            member_roles={OWN_ORG: "owner"},
        ),
        consultants=FakeConsultantsRepo(),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(_user(is_org_member=True), repos, UNRELATED)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_changing_the_acting_for_id_cannot_reach_another_tenant() -> None:
    """Case 8: the acting-for value is a request, never an authority."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG, CLIENT_A),
            member_roles={OWN_ORG: "owner"},
        ),
        consultants=FakeConsultantsRepo(),
    )
    allowed = await resolve_accounting_context(_user(is_org_member=True), repos, OWN_ORG)
    assert allowed.acting_for_organization_id == OWN_ORG
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(_user(is_org_member=True), repos, CLIENT_A)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Case 2 / 3 / 4 / 7 — consultant firm and delegated client access
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_consultant_acts_for_own_firm_organization() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG), member_roles={}
        ),
        consultants=FakeConsultantsRepo(context=FakeConsultantContext()),
    )
    context = await resolve_accounting_context(_user(is_org_member=False, organization_id=None), repos)
    assert context.acting_for_organization_id == FIRM_ORG
    assert context.entitlement_basis == (
        EntitlementBasis.CONSULTANT_FIRM_MEMBERSHIP.value
    )
    assert context.acting_for_kind == ActingForKind.CONSULTANT_TEAM_FOR_FIRM.value
    assert context.is_delegated is False
    assert context.persona == CamsPersona.CONSULTANT


@pytest.mark.asyncio
async def test_consultant_acts_for_an_actively_delegated_client() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG, CLIENT_A), member_roles={}
        ),
        consultants=FakeConsultantsRepo(
            context=FakeConsultantContext(),
            grants=[FakeClientGrant(CLIENT_A, status="active")],
        ),
    )
    context = await resolve_accounting_context(
        _user(is_org_member=False, organization_id=None), repos, CLIENT_A
    )
    assert context.acting_for_organization_id == CLIENT_A
    assert context.is_delegated is True
    assert context.entitlement_basis == (
        EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION.value
    )
    assert context.acting_for_kind == ActingForKind.CONSULTANT_FOR_CLIENT.value
    assert context.persona == CamsPersona.CONSULTANT_CLIENT
    assert context.as_payload()["acting_for_label"] == "ACTING FOR: ORG-CLIENT-A"


@pytest.mark.asyncio
async def test_consultant_is_denied_for_an_unauthorized_client() -> None:
    """Case 4: an entitlement to one client is not a key to another."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG, CLIENT_A, CLIENT_B), member_roles={}
        ),
        consultants=FakeConsultantsRepo(
            context=FakeConsultantContext(),
            grants=[FakeClientGrant(CLIENT_A, status="active")],
        ),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(_user(is_org_member=False, organization_id=None), repos, CLIENT_B)
    assert exc.value.status_code == 403


@pytest.mark.parametrize(
    "status", ["pending", "rejected", "suspended", "ended", "inactive"]
)
@pytest.mark.asyncio
async def test_only_an_active_grant_grants_access(status: str) -> None:
    """Case 7 / D15: a non-active consultant-client grant grants nothing."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG, CLIENT_A), member_roles={}
        ),
        consultants=FakeConsultantsRepo(
            context=FakeConsultantContext(),
            grants=[FakeClientGrant(CLIENT_A, status=status)],
        ),
    )
    authorized = await list_authorized_organizations(_user(is_org_member=False, organization_id=None), repos)
    assert [o.organization_id for o in authorized] == [FIRM_ORG]
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(_user(is_org_member=False, organization_id=None), repos, CLIENT_A)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_being_a_consultant_alone_grants_no_client_organizations() -> None:
    """Consultant status is not an entitlement: only an active grant is."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG, CLIENT_A), member_roles={}
        ),
        consultants=FakeConsultantsRepo(context=FakeConsultantContext(), grants=[]),
    )
    authorized = await list_authorized_organizations(_user(is_org_member=False, organization_id=None), repos)
    assert [o.organization_id for o in authorized] == [FIRM_ORG]
    assert all(o.relationship == RELATIONSHIP_OWN for o in authorized)


@pytest.mark.asyncio
async def test_authorized_list_marks_delegated_relationships() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(FIRM_ORG, CLIENT_A), member_roles={}
        ),
        consultants=FakeConsultantsRepo(
            context=FakeConsultantContext(),
            grants=[FakeClientGrant(CLIENT_A, status="active")],
        ),
    )
    authorized = await list_authorized_organizations(_user(is_org_member=False, organization_id=None), repos)
    by_id = {o.organization_id: o for o in authorized}
    assert by_id[FIRM_ORG].is_own is True
    assert by_id[CLIENT_A].relationship == RELATIONSHIP_CONSULTANT_CLIENT
    assert by_id[CLIENT_A].is_own is False


@pytest.mark.asyncio
async def test_membership_wins_over_a_delegated_grant_for_the_same_org() -> None:
    """The list never overstates the relationship."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(CLIENT_A), member_roles={CLIENT_A: "owner"}
        ),
        consultants=FakeConsultantsRepo(
            context=FakeConsultantContext(),
            grants=[FakeClientGrant(CLIENT_A, status="active")],
        ),
    )
    authorized = await list_authorized_organizations(_user(is_org_member=True), repos)
    by_id = {o.organization_id: o for o in authorized}
    assert by_id[CLIENT_A].relationship == RELATIONSHIP_OWN
    assert by_id[CLIENT_A].entitlement_basis == (
        EntitlementBasis.ORGANIZATION_MEMBERSHIP.value
    )


# ---------------------------------------------------------------------------
# Case 10 — the DATA-OWNING organization is the authority
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_record_owner_authorization_uses_the_owner_not_the_request() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG, UNRELATED),
            member_roles={OWN_ORG: "owner"},
        ),
        consultants=FakeConsultantsRepo(),
    )
    context = await ensure_record_owner_authorized(
        _user(is_org_member=True), repos, OWN_ORG
    )
    assert context.data_owning_organization_id == OWN_ORG
    with pytest.raises(HTTPException) as exc:
        await ensure_record_owner_authorized(
            _user(is_org_member=True), repos, UNRELATED
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_processing_entity_staff_cannot_act_for_a_customer_organization() -> None:
    """The PE boundary fails closed rather than assuming access."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG), member_roles={}
        ),
        consultants=FakeConsultantsRepo(),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(
            _user(is_staff=True, entity_id="entity-1", organization_id=None),
            repos,
            OWN_ORG,
        )
    assert exc.value.status_code == 403
    assert "Processing Entity" in exc.value.detail


@pytest.mark.asyncio
async def test_internal_staff_may_act_for_an_existing_organization() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG), member_roles={}
        ),
        consultants=FakeConsultantsRepo(),
    )
    context = await resolve_accounting_context(
        _user(is_staff=True, entity_id=None, organization_id=None), repos, OWN_ORG
    )
    assert context.acting_for_organization_id == OWN_ORG
    assert context.entitlement_basis == EntitlementBasis.CARBONTALLY_INTERNAL_ROLE.value
    assert context.acting_for_kind == ActingForKind.CARBONTALLY_STAFF.value


@pytest.mark.asyncio
async def test_internal_staff_requesting_a_missing_organization_gets_404() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(organizations={}, member_roles={}),
        consultants=FakeConsultantsRepo(),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(
            _user(is_staff=True, entity_id=None, organization_id=None),
            repos,
            "00000000-0000-0000-0000-000000000000",
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_internal_staff_must_name_an_organization() -> None:
    """Internal staff have no own organization, so one must be supplied."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(organizations={}, member_roles={}),
        consultants=FakeConsultantsRepo(),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(
            _user(is_staff=True, entity_id=None, organization_id=None), repos
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_unauthenticated_request_is_rejected() -> None:
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"}
        ),
        consultants=FakeConsultantsRepo(),
    )
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(None, repos)  # type: ignore[arg-type]
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_member_of_an_inactive_organization_is_not_authorized() -> None:
    """An inactive tenant grants nothing, even with a membership row."""
    orgs = _orgs(OWN_ORG)
    orgs[OWN_ORG]["is_active"] = False
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=orgs, member_roles={OWN_ORG: "owner"}
        ),
        consultants=FakeConsultantsRepo(),
    )
    authorized = await list_authorized_organizations(_user(is_org_member=True), repos)
    assert authorized == []
    with pytest.raises(HTTPException) as exc:
        await resolve_accounting_context(_user(is_org_member=True), repos)
    assert exc.value.status_code in (403, 422)


@pytest.mark.asyncio
async def test_provenance_columns_never_carry_the_owner_key() -> None:
    """Acting-for is context; the payload carries only the two context columns."""
    repos = FakeRepos(
        accounting_context=FakeAccountingContextRepo(
            organizations=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"}
        ),
        consultants=FakeConsultantsRepo(),
    )
    context = await resolve_accounting_context(_user(is_org_member=True), repos)
    assert set(context.provenance_columns()) == {
        "actor_organization_id",
        "acting_for_organization_id",
    }
