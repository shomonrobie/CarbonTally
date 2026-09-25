"""P17-IMPLEMENT-03 — acting-for attribution on the supplier write path.

Exercises the REAL route (`POST /api/v3/suppliers`) through TestClient, so the
test proves the wiring — context resolution -> repository call -> persisted
attribution -> audit — rather than calling the attribution helper in isolation.

The supplier repository is replaced by a recording fake so no database is needed;
the fake captures the ``provenance`` payload the route actually passes, which is
exactly the value written to ``suppliers.actor_organization_id`` /
``suppliers.acting_for_organization_id``.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.dependencies import get_repositories
from api.v3_suppliers import router as suppliers_router
from auth import AuthUser, get_current_user
from core.exceptions import CarbonTallyError

OWN_ORG = "11111111-1111-4111-8111-111111111111"
CLIENT_A = "22222222-2222-4222-8222-222222222222"
UNRELATED = "33333333-3333-4333-8333-333333333333"
FIRM_ORG = "44444444-4444-4444-8444-444444444444"
USER_ID = "66666666-6666-4666-8666-666666666666"
SUPPLIER_ID = "99999999-9999-4999-8999-999999999999"


class _SupplierRepo:
    """Records every create call, including the provenance payload."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(id=SUPPLIER_ID, organization_id=kwargs["org_id"])


class _OrgRepo:
    def __init__(self, orgs: dict[str, dict], member_roles: dict[str, str]) -> None:
        self._orgs = orgs
        self._member_roles = member_roles

    async def get_organization_summary(self, organization_id: str):
        return self._orgs.get(organization_id)

    async def list_active_member_roles(self, user_id: str) -> dict[str, str]:
        return dict(self._member_roles)


class _Grant:
    def __init__(self, organization_id: str, status: str) -> None:
        self.organization_id = organization_id
        self.client_name = "Client"
        self.status = status


class _Profile:
    id = "profile-1"
    user_id = "u-firm"
    company_name = "Green Advisory"
    organization_id = FIRM_ORG
    is_active = True


class _Membership:
    firm_id = "profile-1"
    joined_at = None
    invited_at = None


class _ConsultantRepo:
    """A consultant firm member with the given client grants."""

    def __init__(self, grants=None, is_consultant: bool = True) -> None:
        self._grants = grants or []
        self._is_consultant = is_consultant

    async def get_active_memberships_by_user(self, user_id: str):
        return [_Membership()] if self._is_consultant else []

    async def get_profile_by_id(self, firm_id: str):
        return _Profile() if self._is_consultant else None

    async def list_clients(self, consultant_id: str):
        return list(self._grants)

    async def get_client_by_org(self, consultant_id: str, organization_id: str):
        for grant in self._grants:
            if grant.organization_id == organization_id:
                return grant
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


def _bundle(orgs, member_roles, consultants=None):
    class _Bundle:
        def __init__(self) -> None:
            self.suppliers = _SupplierRepo()
            self.accounting_context = _OrgRepo(orgs, member_roles)
            self.consultants = consultants or _ConsultantRepo(is_consultant=False)
            self.audit = _AuditRepo()

    return _Bundle()


def _app(user: AuthUser, repos) -> FastAPI:
    app = FastAPI()
    app.include_router(suppliers_router)

    @app.exception_handler(CarbonTallyError)
    async def _handler(request, exc: CarbonTallyError):  # noqa: ANN001
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_repositories] = lambda: repos
    return app


def _member() -> AuthUser:
    return AuthUser(
        user_id=USER_ID,
        email="m@example.com",
        role="org_owner",
        role_name="owner",
        organization_id=OWN_ORG,
        is_org_member=True,
        is_admin=True,
    )


def _consultant() -> AuthUser:
    return AuthUser(
        user_id=USER_ID,
        email="c@example.com",
        role="org_owner",
        role_name="owner",
        organization_id=None,
        is_org_member=False,
        is_admin=False,
    )


def _payload(org: str) -> dict:
    return {"organization_id": org, "name": "Acme Fuels"}


# ---------------------------------------------------------------------------
# Case 1 — direct customer writing their own record succeeds and is attributed
# ---------------------------------------------------------------------------
def test_direct_customer_supplier_write_records_acting_for_own_organization() -> None:
    repos = _bundle(_orgs(OWN_ORG), {OWN_ORG: "owner"})
    client = TestClient(_app(_member(), repos))
    response = client.post("/api/v3/suppliers", json=_payload(OWN_ORG))
    assert response.status_code == 201
    provenance = repos.suppliers.calls[-1]["provenance"]
    assert provenance == {
        "actor_organization_id": OWN_ORG,
        "acting_for_organization_id": OWN_ORG,
    }
    # The audit ledger carries the same attribution plus the data owner.
    assert len(repos.audit.entries) == 1
    entry = repos.audit.entries[0]
    assert entry.acting_for_organization_id == OWN_ORG
    assert entry.organization_id == OWN_ORG
    assert entry.entity_type == "supplier"
    assert entry.entity_id == SUPPLIER_ID
    assert entry.action == "acting_for_attributed"


# ---------------------------------------------------------------------------
# Cases 5 / 8 — writing another tenant's records is refused, nothing written
# ---------------------------------------------------------------------------
def test_writing_an_unrelated_organizations_supplier_is_refused() -> None:
    repos = _bundle(_orgs(OWN_ORG, UNRELATED), {OWN_ORG: "owner"})
    client = TestClient(_app(_member(), repos))
    response = client.post("/api/v3/suppliers", json=_payload(UNRELATED))
    assert response.status_code == 403
    assert repos.suppliers.calls == []
    assert repos.audit.entries == []


# ---------------------------------------------------------------------------
# Cases 6 / 10 — a forged acting-for cannot influence the attribution
# ---------------------------------------------------------------------------
def test_forged_acting_for_in_the_payload_cannot_change_the_attribution() -> None:
    repos = _bundle(_orgs(OWN_ORG), {OWN_ORG: "owner"})
    client = TestClient(_app(_member(), repos))
    response = client.post(
        "/api/v3/suppliers",
        json={**_payload(OWN_ORG), "acting_for_organization_id": UNRELATED},
    )
    assert response.status_code == 201
    provenance = repos.suppliers.calls[-1]["provenance"]
    assert provenance["acting_for_organization_id"] == OWN_ORG


# ---------------------------------------------------------------------------
# Cases 2 / 3 / 4 / 9 — consultant delegation on the supplier write
# ---------------------------------------------------------------------------
def test_consultant_cannot_reach_the_supplier_route_through_the_existing_admin_gate() -> None:
    """DISCOVERED BLOCKER (documented, not worked around).

    ``POST /api/v3/suppliers`` is gated by the PRE-EXISTING ``require_org_admin()``
    dependency, which accepts only an internal CarbonTally admin or an
    organisation member whose role is ``owner``/``admin``. A consultant firm
    member acting for a delegated client satisfies neither, so the route refuses
    before the accounting context is ever resolved.

    The P17 acting-for wiring on this route is therefore correct and tested for
    the personas the route admits, but consultant-delegated supplier creation
    cannot happen on this route until the route's authorization is widened —
    which is a P16 authorization change and deliberately OUT OF SCOPE here.
    Widening it would alter existing business behaviour, which this task forbids.
    """
    repos = _bundle(
        _orgs(FIRM_ORG, CLIENT_A), {}, _ConsultantRepo([_Grant(CLIENT_A, "active")])
    )
    client = TestClient(_app(_consultant(), repos))
    response = client.post("/api/v3/suppliers", json=_payload(CLIENT_A))
    assert response.status_code == 403
    # Refused by the admin gate, so no write and no attribution occurred.
    assert repos.suppliers.calls == []
    assert repos.audit.entries == []


def test_the_accounting_context_itself_authorizes_consultant_delegation() -> None:
    """The P17 layer DOES resolve consultant delegation for this organization.

    Proves the blocker above is the route's P16 admin gate and not the P17
    accounting context: resolving the context for the same actor and client
    succeeds and yields the delegated acting-for organization.
    """
    import asyncio

    from api.accounting_context_auth import resolve_accounting_context

    repos = _bundle(
        _orgs(FIRM_ORG, CLIENT_A), {}, _ConsultantRepo([_Grant(CLIENT_A, "active")])
    )
    context = asyncio.run(
        resolve_accounting_context(_consultant(), repos, CLIENT_A)
    )
    assert context.acting_for_organization_id == CLIENT_A
    assert context.actor_organization_id == FIRM_ORG
    assert context.is_delegated is True
    assert context.provenance_columns()["acting_for_organization_id"] == CLIENT_A


def test_consultant_own_firm_organization_is_accepted_by_the_accounting_context() -> None:
    """Same separation for the consultant's own firm organization."""
    import asyncio

    from api.accounting_context_auth import resolve_accounting_context

    repos = _bundle(_orgs(FIRM_ORG), {}, _ConsultantRepo([]))
    context = asyncio.run(resolve_accounting_context(_consultant(), repos, FIRM_ORG))
    assert context.acting_for_organization_id == FIRM_ORG
    assert context.acting_for_kind == "CONSULTANT_TEAM_FOR_FIRM"


# ---------------------------------------------------------------------------
# Backward compatibility — an existing caller that passes no provenance
# ---------------------------------------------------------------------------
def test_supplier_repository_still_accepts_a_call_without_provenance() -> None:
    """The provenance parameter is optional, so P16 callers are unchanged."""
    import inspect

    from data.suppliers import SuppliersRepository

    signature = inspect.signature(SuppliersRepository.create)
    parameter = signature.parameters["provenance"]
    assert parameter.default is None
    assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
