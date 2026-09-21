"""I2 — CarbonTally Insight authorization matrix (ALLOW and DENY).

Authorization: `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (I2 only).

Verifies the ratified access model against the **real** authorization paths:

* customer → own organization membership (D2 §9.5 / PO decision);
* consultant → the existing D15 ``consultant_clients`` ACTIVE grant
  (``api.consultant_auth.ensure_consultant_org_access``);
* internal staff → the existing ACTIVE ``staff_profiles`` profile
  (``api.operations_auth.resolve_staff_context``, ``entity_id IS NULL``);
* auditors / PE / public → denied (PO decision, D2 §10.4);
* creator-private visibility for every persona (D2 §9.2);
* every read re-authorized; stored ids and scope parameters are never grants
  (D2 §8.2/§8.4/§8.8).

The repositories behind the real resolvers are replaced with in-memory fakes that
implement the *same surfaces* the platform resolvers call, so the tests exercise
the production authorization code path rather than a re-implementation.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from api import insight_authz, v3_insight
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from domain.staff import StaffProfile, StaffRole

from tests.unit.api.test_v3_insight_endpoints import (
    ALICE,
    BASE,
    BOB,
    ORG_A,
    ORG_B,
    InMemoryInsightRepository,
)

ORG_C = "33333333-3333-4333-8333-333333333333"
CONSULTANT = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
STAFF = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
FIRM = "ffffffff-ffff-4fff-8fff-ffffffffffff"
#: The exact role strings `auth.py` produces for organisation members
#: (``role = f"org_{org_role}"``): OHD I2 F-01.
ALL_ROLES = ("org_owner", "org_admin", "org_member", "org_viewer")


# --------------------------------------------------------------------------
# In-memory stand-ins for the surfaces the real resolvers call
# --------------------------------------------------------------------------
class _StaffRepo:
    """``StaffRepository`` surface used by ``operations_auth._resolve_context``."""

    def __init__(self) -> None:
        self.profiles: dict[str, StaffProfile] = {}
        self.roles: dict[str, StaffRole] = {}

    def add_profile(self, user_id: str, *, entity_id=None, role_id=None, is_active=True):
        profile = StaffProfile(
            id=f"profile-{user_id[:8]}",
            user_id=user_id,
            first_name="Staff",
            last_name="Member",
            email=f"{user_id[:8]}@carbontally.test",
            role_id=role_id,
            is_active=is_active,
            entity_id=entity_id,
        )
        self.profiles[user_id] = profile
        return profile

    async def get_by_user(self, user_id: str):
        return self.profiles.get(user_id)

    async def get_role(self, role_id: str):
        return self.roles.get(role_id)


class _ConsultantRepo:
    """``ConsultantsRepository`` surface used by ``consultant_auth``."""

    def __init__(self) -> None:
        self.memberships: dict[str, list] = {}
        self.profiles: dict[str, object] = {}
        self.grants: dict[tuple[str, str], object] = {}

    def add_firm_member(self, user_id: str, firm_id: str = FIRM):
        member = type("M", (), {"firm_id": firm_id, "joined_at": None, "invited_at": None})()
        self.memberships.setdefault(user_id, []).append(member)
        self.profiles[firm_id] = type("P", (), {"id": firm_id, "is_active": True})()

    def grant(self, organization_id: str, status: str = "active", firm_id: str = FIRM):
        self.grants[(firm_id, organization_id)] = type("G", (), {"status": status})()

    async def get_active_memberships_by_user(self, user_id: str):
        return self.memberships.get(user_id, [])

    async def get_profile_by_id(self, profile_id: str):
        return self.profiles.get(profile_id)

    async def get_client_by_org(self, consultant_id: str, organization_id: str):
        return self.grants.get((consultant_id, organization_id))


class _OrgRepo:
    """``OrganizationsRepository`` surface used by the OHD-F-02 active check."""

    def __init__(self, active=()):
        self.active = set(active)

    async def get_by_id(self, org_id: str):
        return type("O", (), {"id": org_id, "is_active": org_id in self.active})()


def _bundle(repo, staff=None, consultants=None, orgs=None):
    return type(
        "Bundle",
        (),
        {
            "insight": repo,
            "staff": staff or _StaffRepo(),
            "consultants": consultants or _ConsultantRepo(),
            "organizations": orgs if orgs is not None else _OrgRepo({ORG_A, ORG_B, ORG_C}),
        },
    )()


def _user(
    user_id: str,
    organization_id: str | None = ORG_A,
    *,
    role: str = "org_member",
    is_org_member: bool = True,
    is_staff: bool = False,
    entity_id: str | None = None,
) -> AuthUser:
    """Build a principal the way the platform does.

    `auth.py:313` sets ``role = f"org_{org_role}"`` **and** ``role_name = role``
    for an organisation member, so the default here is the production shape
    (``org_member``), not a bare role (OHD I2 F-01).
    """
    return AuthUser(
        user_id=user_id,
        email=f"{user_id[:8]}@example.test",
        role=role,
        role_name=role,
        organization_id=organization_id,
        is_org_member=is_org_member,
        is_staff=is_staff,
        entity_id=entity_id,
    )


@pytest.fixture()
def api():
    repo = InMemoryInsightRepository()
    staff = _StaffRepo()
    consultants = _ConsultantRepo()
    app = FastAPI()
    app.include_router(v3_insight.router)
    orgs = _OrgRepo({ORG_A, ORG_B, ORG_C})
    state = {
        "user": _user(ALICE, ORG_A, role="org_owner"),
        "unauthenticated": False,
        "repos": _bundle(repo, staff, consultants, orgs),
    }

    async def _current_user():
        if state["unauthenticated"]:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return state["user"]

    async def _repositories():
        return state["repos"]

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    return type(
        "Api",
        (),
        {
            "client": TestClient(app),
            "repo": repo,
            "staff": staff,
            "consultants": consultants,
            "orgs": orgs,
            "state": state,
        },
    )()


def _create(api, organization_id=ORG_A):
    response = api.client.post(
        f"{BASE}/conversations", json={"organization_id": organization_id, "title": "I2"}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _list(api, organization_id):
    return api.client.get(f"{BASE}/conversations", params={"organization_id": organization_id})


# --------------------------------------------------------------------------
# 1/2 — customer authorization and cross-org denial
# --------------------------------------------------------------------------
@pytest.mark.parametrize("role", ALL_ROLES)
def test_customer_uses_insight_in_own_organization_only(api, role):
    api.state["user"] = _user(ALICE, ORG_A, role=role)
    created = _create(api)

    assert _list(api, ORG_A).status_code == 200
    assert (
        api.client.get(
            f"{BASE}/conversations/{created['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 200
    )
    assert (
        api.client.post(
            f"{BASE}/conversations/{created['id']}/messages",
            json={"organization_id": ORG_A, "content": "hello"},
        ).status_code
        == 201
    )
    # Another organisation is refused (scope cannot be expanded by parameter).
    assert _list(api, ORG_B).status_code == 403
    assert api.repo.writes == 2


def test_customer_cannot_read_another_customers_conversation(api):
    conversation = _create(api)  # ORG_A / ALICE
    api.state["user"] = _user(BOB, ORG_A, role="admin")
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 404
    )
    assert _list(api, ORG_A).json()["conversations"] == []


# --------------------------------------------------------------------------
# 3/4/5/6 — consultant authorization via the existing D15 grant
# --------------------------------------------------------------------------
def test_consultant_with_active_grant_may_use_insight_for_that_customer(api):
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    created = _create(api)
    assert created["organization_id"] == ORG_A
    assert _list(api, ORG_A).status_code == 200


def test_consultant_without_an_active_grant_is_denied(api):
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A, status="ended")
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    assert _list(api, ORG_A).status_code == 403
    assert api.repo.writes == 0


def test_consultant_is_denied_for_an_unassigned_customer_even_when_named(api):
    """Naming a customer in the request is not authorization (D2 §8.2)."""
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_B)  # only ORG_B is authorized
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    assert _list(api, ORG_B).status_code == 200
    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.post(
            f"{BASE}/conversations", json={"organization_id": ORG_A, "title": "unassigned"}
        ).status_code
        == 403
    )


def test_consultant_may_use_multiple_authorized_customers_and_stays_creator_private(api):
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A)
    api.consultants.grant(ORG_B)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    for org in (ORG_A, ORG_B):
        assert _create(api, org)["organization_id"] == org
        assert _list(api, org).status_code == 200

    # A customer user cannot see the consultant's conversation, and vice versa.
    consultant_conversation = api.repo.conversations[
        next(
            cid
            for cid, c in api.repo.conversations.items()
            if c.organization_id == ORG_A
        )
    ]
    api.state["user"] = _user(ALICE, ORG_A, role="owner")
    assert (
        api.client.get(
            f"{BASE}/conversations/{consultant_conversation.id}",
            params={"organization_id": ORG_A},
        ).status_code
        == 404
    )


def test_consultant_grant_revocation_ends_access_on_the_next_read(api):
    """D2 §8.8 — revocation must end access to existing conversations."""
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)
    conversation = _create(api)

    api.consultants.grants[(FIRM, ORG_A)] = type("G", (), {"status": "ended"})()
    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 403
    )


# --------------------------------------------------------------------------
# 7 — staff/admin internal scope (existing staff profile, not org membership)
# --------------------------------------------------------------------------
def test_internal_staff_gets_internal_scope_from_an_active_staff_profile(api):
    api.staff.roles["r-admin"] = StaffRole(
        id="r-admin", name="admin", permissions={"can_view_all": True}
    )
    api.staff.add_profile(STAFF, entity_id=None, role_id="r-admin")
    # A staff principal who is ALSO an org member of ORG_B: staff scope must be
    # resolved from the staff profile, never inferred from customer membership.
    api.state["user"] = _user(STAFF, ORG_B, role="member", is_org_member=True, is_staff=True)

    for org in (ORG_A, ORG_B):
        created = _create(api, org)
        assert created["organization_id"] == org
        assert _list(api, org).status_code == 200

    assert insight_authz.resolve_insight_persona(api.state["user"]) == "staff_internal"


def test_staff_shaped_identity_without_an_active_profile_gains_no_staff_scope(api):
    api.staff.add_profile(STAFF, entity_id=None, is_active=False)
    api.state["user"] = _user(STAFF, ORG_B, role="member", is_org_member=True, is_staff=True)

    # Falls through to the ordinary customer rule: own organisation only.
    assert _list(api, ORG_B).status_code == 200
    assert _list(api, ORG_A).status_code == 403


def test_staff_remain_creator_private_on_the_insight_surface(api):
    """The PO decision authorizes staff *use*, not reading others' conversations."""
    conversation = _create(api)  # ALICE / ORG_A
    api.staff.roles["r-ops"] = StaffRole(id="r-ops", name="admin", permissions={"can_view_all": True})
    api.staff.add_profile(STAFF, entity_id=None, role_id="r-ops")
    api.state["user"] = _user(
        STAFF, ORG_A, role="operator", is_org_member=True, is_staff=True
    )

    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 404
    )
    assert _list(api, ORG_A).json()["conversations"] == []


# --------------------------------------------------------------------------
# 8/9/10 — denied personas
# --------------------------------------------------------------------------
def test_processing_entity_staff_are_denied_outright(api):
    api.state["user"] = _user(
        STAFF, None, role="pe_manager", is_org_member=False, is_staff=True, entity_id="ent-1"
    )
    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.post(
            f"{BASE}/conversations", json={"organization_id": ORG_A, "title": "pe"}
        ).status_code
        == 403
    )
    assert api.repo.writes == 0


def test_pe_staff_profile_is_denied_even_if_the_identity_flags_disagree(api):
    """The staff *profile* is authoritative: entity_id set = PE = no Insight."""
    api.staff.add_profile(STAFF, entity_id="ent-1")
    api.state["user"] = _user(STAFF, None, role="operator", is_org_member=False, is_staff=True)
    assert _list(api, ORG_A).status_code == 403


@pytest.mark.parametrize("role", ("auditor", "org_auditor", "assurance_reviewer"))
def test_auditor_persona_is_explicitly_denied(api, role):
    """OHD I2 O-01 — named refusal, not implicit fall-through."""
    api.state["user"] = _user(
        "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee", ORG_A, role=role, is_org_member=True
    )
    assert insight_authz.resolve_insight_persona(api.state["user"]) == "auditor"
    assert insight_authz.is_auditor_principal(api.state["user"]) is True
    assert _list(api, ORG_A).status_code == 403
    assert api.repo.writes == 0


def test_public_or_unauthenticated_callers_are_denied_with_a_challenge(api):
    api.state["unauthenticated"] = True
    response = _list(api, ORG_A)
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


# --------------------------------------------------------------------------
# 11/12/13/14/15 — invariants
# --------------------------------------------------------------------------
def test_membership_revocation_ends_access_to_existing_conversations(api):
    conversation = _create(api)
    api.state["user"] = _user(ALICE, None, role="member", is_org_member=False)
    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 403
    )


def test_guessed_conversation_id_cannot_bypass_authorization(api):
    conversation = _create(api)
    # A consultant authorized for ORG_A but not the creator still sees nothing.
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 404
    )
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}/messages",
            params={"organization_id": ORG_A},
        ).status_code
        == 404
    )


def test_author_kind_cannot_be_forged_through_the_api(api):
    conversation = _create(api)
    writes_before = api.repo.writes
    assert (
        api.client.post(
            f"{BASE}/conversations/{conversation['id']}/messages",
            json={"organization_id": ORG_A, "content": "forged", "role": "insight"},
        ).status_code
        == 422
    )
    assert api.repo.writes == writes_before


def test_every_insight_route_carries_the_gate_by_construction():
    gate = insight_authz.require_insight_user
    assert any(
        getattr(dep, "dependency", None) is gate for dep in v3_insight.router.dependencies
    )


def test_persona_decision_table_enumerates_every_persona():
    assert set(insight_authz.PERSONA_DECISIONS) == {
        "customer",
        "consultant",
        "staff_internal",
        "processing_entity",
        "auditor",
        "non_member",
        "unauthenticated",
    }
    allows = {p for p, d in insight_authz.PERSONA_DECISIONS.items() if d.startswith("ALLOW")}
    assert allows == {"customer", "consultant", "staff_internal"}
    assert insight_authz.INSIGHT_VISIBILITY_MODEL == "creator_private"


# --------------------------------------------------------------------------
# OHD I2 F-02 — the organisation must be ACTIVE
# --------------------------------------------------------------------------
def test_customer_is_denied_for_an_inactive_organization(api):
    api.state["user"] = _user(ALICE, ORG_A, role="org_owner")
    api.orgs.active.discard(ORG_A)

    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.post(
            f"{BASE}/conversations", json={"organization_id": ORG_A, "title": "suspended"}
        ).status_code
        == 403
    )
    assert api.repo.writes == 0


def test_organization_suspension_takes_effect_on_the_next_read(api):
    api.state["user"] = _user(ALICE, ORG_A, role="org_owner")
    conversation = _create(api)

    api.orgs.active.discard(ORG_A)
    assert _list(api, ORG_A).status_code == 403
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 403
    )

    api.orgs.active.add(ORG_A)  # restoration returns access
    assert _list(api, ORG_A).status_code == 200


def test_consultant_is_denied_for_an_inactive_customer_organization(api):
    api.consultants.add_firm_member(CONSULTANT)
    api.consultants.grant(ORG_A)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)

    assert _list(api, ORG_A).status_code == 200  # active customer + active grant
    api.orgs.active.discard(ORG_A)
    assert _list(api, ORG_A).status_code == 403  # grant survives, organisation does not


def test_unknown_organization_is_denied(api):
    api.state["user"] = _user(ALICE, ORG_A, role="org_owner")
    assert _list(api, "99999999-9999-4999-8999-999999999999").status_code == 403


# --------------------------------------------------------------------------
# OHD I2 O-02 — staff scope is bound to existing staff permissions
# --------------------------------------------------------------------------
def test_staff_without_the_ops_permission_gains_no_staff_scope(api):
    """Staff identity alone must not invent cross-organisation access."""
    api.staff.roles["r-op"] = StaffRole(
        id="r-op", name="operator", permissions={"can_process": True}
    )
    api.staff.add_profile(STAFF, entity_id=None, role_id="r-op")
    api.state["user"] = _user(STAFF, ORG_B, role="operator", is_org_member=True, is_staff=True)

    # Deny-by-default: the principal carries the *staff* role, so no customer
    # scope is invented from membership either.
    assert _list(api, ORG_A).status_code == 403
    assert _list(api, ORG_B).status_code == 403
    assert api.repo.writes == 0


def test_staff_with_the_ops_permission_receives_internal_scope(api):
    api.staff.roles["r-ops"] = StaffRole(
        id="r-ops", name="admin", permissions={"can_view_all": True}
    )
    api.staff.add_profile(STAFF, entity_id=None, role_id="r-ops")
    api.state["user"] = _user(
        STAFF, None, role="admin", is_org_member=False, is_staff=True
    )
    assert _list(api, ORG_A).status_code == 200


def test_superuser_flag_grants_internal_scope(api):
    api.staff.roles["r-sys"] = StaffRole(
        id="r-sys", name="system_admin", permissions={"is_superuser": True}
    )
    api.staff.add_profile(STAFF, entity_id=None, role_id="r-sys")
    api.state["user"] = _user(
        STAFF, None, role="system_admin", is_org_member=False, is_staff=True
    )
    assert _list(api, ORG_A).status_code == 200


def test_staff_scope_helpers_are_bound_to_the_existing_vocabulary(api):
    assert insight_authz.STAFF_INSIGHT_PERMISSIONS == ("can_view_all",)
    permitted = type("C", (), {"permissions": {"can_view_all": True}})()
    denied = type("C", (), {"permissions": {"can_process": True}})()
    empty = type("C", (), {"permissions": None})()
    assert insight_authz.staff_context_grants_insight_scope(permitted) is True
    assert insight_authz.staff_context_grants_insight_scope(denied) is False
    assert insight_authz.staff_context_grants_insight_scope(empty) is False


# --------------------------------------------------------------------------
# OHD I2 F-01 — the role contract
# --------------------------------------------------------------------------
def test_role_normalization_accepts_production_and_bare_forms(api):
    assert insight_authz.normalize_org_role("org_owner") == "owner"
    assert insight_authz.normalize_org_role("owner") == "owner"
    assert insight_authz.normalize_org_role("ORG_ADMIN") == "admin"
    assert insight_authz.normalize_org_role("org_viewer") == "viewer"
    assert insight_authz.normalize_org_role("auditor") == "auditor"
    assert insight_authz.normalize_org_role(None) == ""


def test_unratified_customer_role_is_denied_even_with_membership(api):
    api.state["user"] = _user(ALICE, ORG_A, role="org_supervisor", is_org_member=True)
    assert _list(api, ORG_A).status_code == 403
