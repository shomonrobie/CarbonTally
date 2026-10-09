"""CT-CARBONTALLY-FOUNDATION-CLOSURE-02 — I-02: the CLIENT-ACCESS CEILING on the
supplier write path (``POST`` / ``PUT`` / ``DELETE /api/v3/suppliers``).

Finding (baseline-01 / inventory-02 §1.2 I-02): the supplier write routes declared
``require_org_admin`` but **not** ``require_client_operation("edit_master_data")``,
while facilities, assets and vehicles declared both — so the same master-data
plane enforced the client-access ceiling on three of four resources and not on
the fourth.

These tests exercise the REAL router through ``TestClient`` and assert BOTH
directions (AGENTS §45/§72):

* ALLOW — a direct customer org owner writes; a COLLABORATIVE client writes;
* ALLOW — the ceiling is IDENTITY-scoped: a consultant principal and internal
  staff are never "client users", so the guard does not apply to them even when
  the organisation carries a MANAGED relationship;
* DENY  — a consultant-managed client's own user is refused 403 by the ceiling
  for MANAGED / READ_ONLY / OFF / RETAINED profiles on create, update and delete;
* DENY  — unauthenticated, a non-admin member (pre-existing admin gate) and a
  foreign organisation (pre-existing tenant guard).

No database is required: the supplier repository is a recording fake.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.client_access_guard import (
    CLIENT_OPERATION_DENIED_DETAIL,
    enforce_client_operation,
)
from api.dependencies import get_repositories
from api.v3_suppliers import router as suppliers_router
from auth import AuthUser, get_current_user
from core.exceptions import CarbonTallyError
from domain.relationship_access import (
    PROFILE_COLLABORATIVE,
    PROFILE_MANAGED,
    PROFILE_OFF,
    PROFILE_READ_ONLY,
)

OWN_ORG = "11111111-1111-4111-8111-111111111111"
UNRELATED = "33333333-3333-4333-8333-333333333333"
USER_ID = "66666666-6666-4666-8666-666666666666"
SUPPLIER_ID = "99999999-9999-4999-8999-999999999999"


class _SupplierRepo:
    """Records writes; never touches a database."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.writes: list[tuple] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=SUPPLIER_ID, organization_id=kwargs["org_id"])

    async def get(self, supplier_id: str):
        return SimpleNamespace(id=SUPPLIER_ID, organization_id=OWN_ORG, name="Acme")

    async def update(self, *args, **kwargs):
        self.writes.append(("update", args))
        return SimpleNamespace(id=SUPPLIER_ID, organization_id=OWN_ORG)

    async def remove(self, supplier_id: str) -> None:
        self.writes.append(("remove", supplier_id))


class _OrgRepo:
    def __init__(self, orgs: dict[str, dict], member_roles: dict[str, str]) -> None:
        self._orgs = orgs
        self._member_roles = member_roles

    async def get_organization_summary(self, organization_id: str):
        return self._orgs.get(organization_id)

    async def list_active_member_roles(self, user_id: str) -> dict[str, str]:
        return dict(self._member_roles)


class _Relationship:
    """The authoritative ``consultant_clients`` row the ceiling reads."""

    def __init__(self, profile: str, *, status: str = "active", retained: bool = False):
        self.id = "rel-1"
        self.client_access_profile = profile
        self.status = status
        self.retained_read_only = retained


class _ConsultantsRepo:
    """Minimal consultant repository surface (mirrors the p17 write-path harness)."""

    def __init__(self, relationship: "_Relationship | None" = None) -> None:
        self._relationship = relationship

    async def get_relationship_for_org(self, organization_id: str):
        return self._relationship

    async def get_active_memberships_by_user(self, user_id: str):
        return []

    async def get_profile_by_id(self, firm_id: str):
        return None

    async def list_clients(self, consultant_id: str):
        return []

    async def get_client_by_org(self, consultant_id: str, organization_id: str):
        return None


class _AuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry


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


def _bundle(relationship: "_Relationship | None" = None):
    class _Bundle:
        def __init__(self) -> None:
            self.suppliers = _SupplierRepo()
            self.accounting_context = _OrgRepo(
                _orgs(OWN_ORG, UNRELATED), {OWN_ORG: "owner"}
            )
            self.consultants = _ConsultantsRepo(relationship)
            self.audit = _AuditRepo()

    return _Bundle()


def _app(user, repos) -> FastAPI:
    app = FastAPI()
    app.include_router(suppliers_router)

    @app.exception_handler(CarbonTallyError)
    async def _handler(request, exc: CarbonTallyError):  # noqa: ANN001
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    # ``user`` may be an ``AuthUser`` (the usual case) or a zero-argument callable
    # that resolves/refuses authentication (the unauthenticated case).
    app.dependency_overrides[get_current_user] = (
        user if callable(user) else (lambda: user)
    )
    app.dependency_overrides[get_repositories] = lambda: repos
    return app


def _owner(org: str = OWN_ORG, *, user_id: str = USER_ID) -> AuthUser:
    """An organisation owner/admin (satisfies the pre-existing admin gate)."""
    return AuthUser(
        user_id=user_id,
        email="owner@client.test",
        role="org_owner",
        role_name="owner",
        organization_id=org,
        is_org_member=True,
        is_admin=True,
    )


def _unauthenticated() -> AuthUser:
    raise HTTPException(status_code=401, detail="Not authenticated")


def _payload(org: str = OWN_ORG) -> dict:
    return {"organization_id": org, "name": "Acme Fuels"}


def _error_message(response) -> str:
    """The denial message, from either envelope shape.

    In the running application ``api/middleware.py`` wraps ``HTTPException`` in
    the custom ``{"error": {"message": ...}}`` envelope; this DB-free harness
    includes only the router, so a guard's ``HTTPException(403, detail=...)``
    surfaces as ``{"detail": ...}``. Both carry the same message.
    """
    body = response.json()
    if isinstance(body, dict) and "error" in body:
        return body["error"]["message"]
    return body.get("detail", "")


# ---------------------------------------------------------------------------
# ALLOW — direct customer and collaborative client
# ---------------------------------------------------------------------------
def test_direct_customer_org_owner_may_create_a_supplier():
    """REGRESSION — no consultant relationship → the ceiling does not apply."""
    repos = _bundle()
    client = TestClient(_app(_owner(), repos))
    response = client.post("/api/v3/suppliers", json=_payload())
    assert response.status_code == 201
    assert len(repos.suppliers.calls) == 1


def test_collaborative_client_may_create_a_supplier():
    repos = _bundle(_Relationship(PROFILE_COLLABORATIVE))
    client = TestClient(_app(_owner(), repos))
    assert client.post("/api/v3/suppliers", json=_payload()).status_code == 201


# ---------------------------------------------------------------------------
# DENY — the client-access ceiling (the I-02 defect)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF])
def test_client_profile_denies_supplier_create(profile):
    repos = _bundle(_Relationship(profile))
    client = TestClient(_app(_owner(), repos))
    response = client.post("/api/v3/suppliers", json=_payload())
    assert response.status_code == 403
    assert _error_message(response) == CLIENT_OPERATION_DENIED_DETAIL
    assert repos.suppliers.calls == []


def test_retained_read_only_client_denies_supplier_create():
    repos = _bundle(_Relationship(PROFILE_MANAGED, status="ended", retained=True))
    client = TestClient(_app(_owner(), repos))
    response = client.post("/api/v3/suppliers", json=_payload())
    assert response.status_code == 403
    assert _error_message(response) == CLIENT_OPERATION_DENIED_DETAIL
    assert repos.suppliers.calls == []


@pytest.mark.parametrize("profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF])
def test_client_profile_denies_supplier_update_and_delete(profile):
    """The ceiling must bind every supplier write, not only create."""
    repos = _bundle(_Relationship(profile))
    client = TestClient(_app(_owner(), repos))
    updated = client.put(f"/api/v3/suppliers/{SUPPLIER_ID}", json={"name": "Renamed"})
    deleted = client.delete(f"/api/v3/suppliers/{SUPPLIER_ID}")
    assert updated.status_code == 403
    assert _error_message(updated) == CLIENT_OPERATION_DENIED_DETAIL
    assert deleted.status_code == 403
    assert _error_message(deleted) == CLIENT_OPERATION_DENIED_DETAIL
    assert repos.suppliers.writes == []


# ---------------------------------------------------------------------------
# DENY — the pre-existing guards are unchanged
# ---------------------------------------------------------------------------
def test_unauthenticated_actor_is_refused():
    repos = _bundle()
    client = TestClient(_app(_unauthenticated, repos))
    assert client.post("/api/v3/suppliers", json=_payload()).status_code == 401
    assert repos.suppliers.calls == []


def test_non_admin_member_is_refused_by_the_admin_gate():
    member = AuthUser(
        user_id=USER_ID,
        email="member@client.test",
        role="org_member",
        role_name="member",
        organization_id=OWN_ORG,
        is_org_member=True,
        is_admin=False,
    )
    repos = _bundle()
    client = TestClient(_app(member, repos))
    response = client.post("/api/v3/suppliers", json=_payload())
    assert response.status_code == 403
    # refused by the pre-existing admin gate, not by the ceiling
    assert CLIENT_OPERATION_DENIED_DETAIL not in response.text
    assert repos.suppliers.calls == []


def test_foreign_organisation_is_refused_by_the_tenant_guard():
    """A direct customer (no ceiling) writing another tenant is still refused."""
    repos = _bundle()
    client = TestClient(_app(_owner(), repos))
    response = client.post("/api/v3/suppliers", json=_payload(UNRELATED))
    assert response.status_code == 403
    assert CLIENT_OPERATION_DENIED_DETAIL not in response.text
    assert repos.suppliers.calls == []


# ---------------------------------------------------------------------------
# Identity separation — the ceiling is not applied to a consultant or staff
# ---------------------------------------------------------------------------
def test_ceiling_is_identity_scoped_for_consultant_and_internal_staff():
    """Even with a MANAGED relationship on the org, non-client identities pass."""
    bundle = _bundle(_Relationship(PROFILE_MANAGED))
    consultant = AuthUser(
        user_id=USER_ID,
        email="cons@firm.test",
        role="consultant",
        role_name="consultant",
        organization_id=None,
        is_org_member=False,
        is_admin=False,
    )
    staff = AuthUser(
        user_id="u-staff",
        email="staff@carbontally.test",
        role="ct_operator",
        role_name="operator",
        organization_id=None,
        is_org_member=False,
        is_admin=True,
        is_staff=True,
    )
    # ALLOW for both (no exception raised) ...
    asyncio.run(enforce_client_operation(consultant, bundle, OWN_ORG, "edit_master_data"))
    asyncio.run(enforce_client_operation(staff, bundle, OWN_ORG, "edit_master_data"))
    # ... while the SAME organisation's own client user IS denied (the control).
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            enforce_client_operation(_owner(), bundle, OWN_ORG, "edit_master_data")
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == CLIENT_OPERATION_DENIED_DETAIL



