"""P6-2F — representative synthetic personas.

Built on the EXISTING authorization model (organisation roles, consultant
firms/grants, staff profiles, Processing-Entity scope). No new production role,
capability, permission or grant is created for testing.

Every persona is an ``AuthUser``; the *authorization* comes from the seeded
relationship data (org membership, active grant, staff profile) — never from a
client-supplied claim.
"""
from __future__ import annotations

from auth import AuthUser
from tests.unit.api.fakes import (
    admin_user,
    consultant_user,
    entity_operator_user,
    member_user,
    org_admin_user,
    org_owner_user,
    staff_user,
)

# --- organisation side -----------------------------------------------------------


def org_owner(org_id: str = "org-a", user_id: str = "u-own", email: str = "owner@client.test") -> AuthUser:
    return org_owner_user(org_id, user_id, email)


def org_admin(org_id: str = "org-a", user_id: str = "u-adm", email: str = "admin@client.test") -> AuthUser:
    return org_admin_user(org_id, user_id, email)


def org_member(org_id: str = "org-a", user_id: str = "u-mem", email: str = "member@client.test") -> AuthUser:
    """A plain organisation member (not an approver)."""
    return member_user(org_id, user_id, email)


def org_viewer(org_id: str = "org-a", user_id: str = "u-view", email: str = "viewer@client.test") -> AuthUser:
    """A read-only organisation member (never an approver / never a writer)."""
    return AuthUser(
        user_id=user_id, email=email, role="viewer", role_name="viewer",
        organization_id=org_id, is_org_member=True,
    )


# --- consultant side -------------------------------------------------------------


def consultant_firm_a(user_id: str = "u-firm-a", email: str = "a@firm-a.test") -> AuthUser:
    return consultant_user(user_id, email)


def consultant_firm_b(user_id: str = "u-firm-b", email: str = "b@firm-b.test") -> AuthUser:
    return consultant_user(user_id, email)


def consultant_ungranted(user_id: str = "u-ungranted", email: str = "x@nowhere.test") -> AuthUser:
    """A consultant identity with no seeded membership/grant at all."""
    return consultant_user(user_id, email)


# --- CarbonTally internal / PE ---------------------------------------------------


def internal_qc(user_id: str = "u-qc") -> AuthUser:
    return staff_user(user_id, email=f"{user_id}@carbontally.test", permissions={"can_qc": True})


def internal_reviewer(user_id: str = "u-review") -> AuthUser:
    return staff_user(user_id, email=f"{user_id}@carbontally.test", permissions={"can_review": True})


def internal_ops(user_id: str = "u-ops") -> AuthUser:
    return staff_user(user_id, email=f"{user_id}@carbontally.test", permissions={"can_manage_staff": True})


def pe_operator(entity_id: str = "ent-1", user_id: str = "u-pe") -> AuthUser:
    return entity_operator_user(entity_id, user_id)


def platform_admin() -> AuthUser:
    return admin_user()
