"""D-7 gap closure — F1 / F2 / F3 organisation-lifecycle enforcement.

D-7 decided that *organisation* suspension is enforced by the
organisation-scoped **guards**, never by authentication: while
``organizations.is_active = false`` every organisation-scoped route denies and
no tenant data is read or written. Three surfaces historically escaped that
decision; each section below is the regression that keeps it closed:

* **F1** — ``routes/emissions.py``: five legacy handlers were gated by the
  AUTHENTICATION dependency (``require_auth``) instead of the organisation
  guard, so a suspended tenant's member kept reaching emissions data. The
  record-level exact-tenant ownership rule ``POST /emissions/verify`` needs is
  pinned here as well (the handler writes through the service-role client, so
  RLS is not the boundary).
* **F2** — the audit/evidence reads (``GET /api/v3/reporting/audit-readiness``,
  ``GET /api/v3/reporting/audit-activity``,
  ``GET /api/v3/exports/audit-package.json``) authorised the caller but never
  consulted the organisation lifecycle, so a suspended tenant — or a
  consultant's suspended client — could still pull its audit evidence.
* **F3** — ``routes/document_activity.py``: the document activity/review
  handlers were authenticated-only, and ``/{file_id}/reviews`` read
  ``customer_review_log`` for ANY file id, i.e. across tenants.

Evidence style mirrors ``test_d7_org_lifecycle_decisions.py``: real routers over
an in-memory service-role store, the REAL guards, denial asserted as HTTP 403
with ``ORGANIZATION_SUSPENDED_DETAIL``, and "the handler never ran" asserted
through the recorded store access (``FakeWorld.handler_tables``) or a spy
repository bundle. No Supabase, no network.

Two ORDERING rules F2 introduced are pinned explicitly:

1. The caller's OWN organisation is answered from the principal, so the audit
   path stays query-free (``world.queries == []``) both for an active tenant and
   for its suspension denial.
2. A FOREIGN organisation's lifecycle is read only AFTER authority over it has
   been proven — a caller with no active client grant never triggers a
   cross-tenant lifecycle read.
"""
from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any, Optional

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import auth
from api import dependencies as dependencies_module
from api.dependencies import ensure_org_audit_access
from auth import ORGANIZATION_SUSPENDED_DETAIL
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_owner_user,
    staff_user,
)
from tests.unit.api.test_d7_org_lifecycle_decisions import (
    ORG_A,
    ORG_B,
    FakeWorld,
    _install_store,
    _membership,
    _module_app,
    _org_row,
    _suspended,
)

# ===========================================================================
# Harness — a spy reporting repository (F2) + the principal matrix
# ===========================================================================
class _SpyReporting:
    """Records every audit/evidence read the handler ASKS for.

    The D-7 property under test is "the guard denied before the handler ran", so
    the spy is both the handler-executed witness (``calls``) and a network-free
    stand-in for ``ReportingRepository``.
    """

    def __init__(self) -> None:
        self.calls: list = []

    async def audit_readiness(self, organization_id: str) -> Any:
        self.calls.append(("audit_readiness", organization_id))
        return {"not_assurance": True, "organization_id": organization_id}

    async def org_audit_activity(self, organization_id: str, **kwargs: Any) -> Any:
        self.calls.append(("org_audit_activity", organization_id))
        return {"events": [], "organization_id": organization_id}

    async def audit_package(self, organization_id: str, **kwargs: Any) -> Any:
        self.calls.append(("audit_package", organization_id))
        return {
            "not_assurance": True,
            "organization_id": organization_id,
            "package_hash": "hash-1",
        }


def _audit_app(module, user, reporting: _SpyReporting) -> FastAPI:
    """A standalone app over a REAL audit/evidence router, DB-free.

    ``get_repositories`` is overridden with a spy bundle, so a handler that runs
    leaves a witness in ``reporting.calls`` while a denied request leaves none.
    """
    app = FastAPI()
    app.include_router(module.router)

    async def _principal():
        return user

    def _repos():
        return SimpleNamespace(reporting=reporting, consultants=None)

    app.dependency_overrides[auth.get_current_user] = _principal
    app.dependency_overrides[dependencies_module.get_repositories] = _repos
    return app


def _audit_route(module_path: str) -> Any:
    return importlib.import_module(module_path)


#: The three F2 audit/evidence reads, all of which call
#: ``ensure_org_audit_access`` before touching any audit data.
_F2_AUDIT_ROUTES = [
    pytest.param(
        "api.v3_reporting",
        f"/api/v3/reporting/audit-readiness?organization_id={ORG_A}",
        "audit_readiness",
        id="f2-audit-readiness",
    ),
    pytest.param(
        "api.v3_reporting",
        f"/api/v3/reporting/audit-activity?organization_id={ORG_A}",
        "org_audit_activity",
        id="f2-audit-activity",
    ),
    pytest.param(
        "api.v3_exports",
        f"/api/v3/exports/audit-package.json?organization_id={ORG_A}",
        "audit_package",
        id="f2-audit-package",
    ),
]

#: The roles a suspended tenant was reachable through. Owner AND plain member:
#: the lifecycle denial precedes the owner/admin role admission test, so the
#: answer must be identical for both.
_F2_SUSPENDED_PRINCIPALS = {
    "owner": lambda org: org_owner_user(org, "u-owner", "o@carbontally.test"),
    "member": lambda org: member_user(org, "u-member", "m@carbontally.test"),
}

#: Per-surface proof that the body came from the handler and not from a stub
#: short-circuit: the readiness/package payloads carry the ``not_assurance``
#: disclaimer, while the activity timeline echoes its own organisation.
_F2_PAYLOAD_PROOF = {
    "audit_readiness": ("not_assurance", True),
    "org_audit_activity": ("organization_id", ORG_A),
    "audit_package": ("not_assurance", True),
}


# ===========================================================================
# F2 — audit / evidence exports consult the organisation lifecycle
# ===========================================================================
@pytest.mark.parametrize("module_path,url,repo_call", _F2_AUDIT_ROUTES)
@pytest.mark.parametrize("role", sorted(_F2_SUSPENDED_PRINCIPALS))
def test_f2_suspended_tenant_is_refused_before_the_audit_handler_runs(
    monkeypatch, module_path, url, repo_call, role
):
    """A SUSPENDED tenant's audit/evidence read denies — before the handler.

    The denial must precede BOTH the handler and the owner/admin role admission
    test (that is why the role is parametrized), so a suspended organisation
    yields the one canonical D-7 message to owner, admin, member and viewer.
    """
    world = FakeWorld(organizations=[_org_row(ORG_A, active=False)])
    _install_store(monkeypatch, world)
    reporting = _SpyReporting()
    user = _suspended(_F2_SUSPENDED_PRINCIPALS[role](ORG_A))
    app = _audit_app(_audit_route(module_path), user, reporting)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == ORGANIZATION_SUSPENDED_DETAIL
    # F2's DB-visible proof: no audit/evidence read was requested and no store
    # round trip happened — the own-org lifecycle decision is answered from the
    # principal (D-7 property 1).
    assert reporting.calls == []
    assert world.queries == []


@pytest.mark.parametrize("module_path,url,repo_call", _F2_AUDIT_ROUTES)
def test_f2_active_tenant_still_gets_its_audit_evidence(
    monkeypatch, module_path, url, repo_call
):
    """No over-blocking: an ACTIVE tenant's owner keeps the audit surfaces."""
    world = FakeWorld([_membership("u-owner", ORG_A, "owner")], organizations=[_org_row(ORG_A)])
    _install_store(monkeypatch, world)
    reporting = _SpyReporting()
    user = org_owner_user(ORG_A, "u-owner", "o@carbontally.test")
    app = _audit_app(_audit_route(module_path), user, reporting)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 200, response.text
    field, expected = _F2_PAYLOAD_PROOF[repo_call]
    assert response.json()[field] == expected
    assert reporting.calls == [(repo_call, ORG_A)]
    assert world.queries == []


@pytest.mark.parametrize("module_path,url,repo_call", _F2_AUDIT_ROUTES)
def test_f2_internal_staff_keep_audit_oversight_of_a_suspended_tenant(
    monkeypatch, module_path, url, repo_call
):
    """D-7 exempts CarbonTally internal staff (support re-enable path)."""
    world = FakeWorld(organizations=[_org_row(ORG_A, active=False)])
    _install_store(monkeypatch, world)
    reporting = _SpyReporting()
    app = _audit_app(_audit_route(module_path), staff_user(), reporting)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 200, response.text
    assert reporting.calls == [(repo_call, ORG_A)]
    assert world.queries == []


@pytest.mark.parametrize("module_path,url,repo_call", _F2_AUDIT_ROUTES)
def test_f2_role_admission_is_unchanged_for_an_active_tenant(
    monkeypatch, module_path, url, repo_call
):
    """F2 adds the lifecycle check only — the owner/admin admission stands.

    A plain member of an ACTIVE organisation keeps the historical role denial
    (and still reads no audit data), so the F2 change cannot widen access.
    """
    world = FakeWorld([_membership("u-member", ORG_A, "member")], organizations=[_org_row(ORG_A)])
    _install_store(monkeypatch, world)
    reporting = _SpyReporting()
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _audit_app(_audit_route(module_path), user, reporting)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Audit records require organisation owner/admin access"
    assert reporting.calls == []
    assert world.queries == []


# ===========================================================================
# F2 — ordering: the client's lifecycle is read only AFTER the grant is proven
# ===========================================================================
class _StubConsultants:
    """The slice of ``ConsultantsRepository`` the consultant path touches.

    Mirrors the authoritative chain of ``api.consultant_auth``: one ACTIVE firm
    membership -> an active firm profile -> the client grant for the organisation.
    """

    def __init__(self, grants: Optional[dict] = None, memberships: int = 1) -> None:
        self._grants = dict(grants or {})
        #: How many ACTIVE firm memberships the caller holds. ``0`` means "no
        #: consultant context at all" — the first denial branch of
        #: ``api.consultant_auth``, before any client grant is even considered.
        self._memberships = memberships

    async def get_active_memberships_by_user(self, user_id: str) -> Any:
        if not self._memberships:
            return []
        return [SimpleNamespace(firm_id="firm-1", joined_at=None, invited_at=None)]

    async def get_profile_by_id(self, firm_id: str) -> Any:
        return SimpleNamespace(id=firm_id, is_active=True)

    async def get_client_by_org(self, consultant_id: str, organization_id: str) -> Any:
        status = self._grants.get(organization_id)
        return None if status is None else SimpleNamespace(status=status)


@pytest.mark.parametrize(
    "stub,expected_detail",
    [
        pytest.param(
            _StubConsultants(memberships=0),
            "Consultant access required",
            id="no-consultant-context",
        ),
        pytest.param(
            _StubConsultants(),
            "Consultant is not authorized for this client organization "
            "(active consultant-client grant required)",
            id="no-client-grant",
        ),
    ],
)
@pytest.mark.asyncio
async def test_f2_denied_consultants_never_trigger_a_client_lifecycle_read(
    monkeypatch, stub, expected_detail
):
    """A denied consultant learns nothing — not even the client's lifecycle.

    D-7 property 2, extended to F2: the cross-tenant lifecycle read (an
    ``organizations`` lookup) happens only after authority over the organisation
    has been established, so an unauthorised caller's request stays query-free.
    Both denial branches are covered — no consultant context at all, and a
    consultant with no ACTIVE grant for this client — because BOTH must answer
    without consulting the client's lifecycle.
    """
    world = FakeWorld(organizations=[_org_row(ORG_B, active=False)])
    _install_store(monkeypatch, world)
    repos = SimpleNamespace(consultants=stub)
    user = consultant_user("u-cons", "c@carbontally.test")

    with pytest.raises(HTTPException) as raised:
        await ensure_org_audit_access(user, repos, ORG_B)

    assert raised.value.status_code == 403
    assert raised.value.detail == expected_detail
    # Never the lifecycle message: another tenant's suspension is not disclosed
    # to a caller who holds no authority there.
    assert raised.value.detail != ORGANIZATION_SUSPENDED_DETAIL
    assert world.queries == []


@pytest.mark.asyncio
async def test_f2_active_grant_on_a_suspended_client_denies_audit_evidence(monkeypatch):
    """An ACTIVE consultant-client grant cannot rescue a SUSPENDED client."""
    world = FakeWorld(organizations=[_org_row(ORG_B, active=False)])
    _install_store(monkeypatch, world)
    repos = SimpleNamespace(consultants=_StubConsultants({ORG_B: "active"}))
    user = consultant_user("u-cons", "c@carbontally.test")

    with pytest.raises(HTTPException) as raised:
        await ensure_org_audit_access(user, repos, ORG_B)

    assert raised.value.status_code == 403
    assert raised.value.detail == ORGANIZATION_SUSPENDED_DETAIL
    # The grant was proven first, so ONLY then was the client's lifecycle read —
    # and no audit/evidence table was touched.
    assert world.queried_tables == ["organizations"]
    assert world.handler_tables == []


@pytest.mark.asyncio
async def test_f2_active_grant_on_an_active_client_is_allowed(monkeypatch):
    """No over-blocking for the legitimate consultant-client relationship."""
    world = FakeWorld(organizations=[_org_row(ORG_B, active=True)])
    _install_store(monkeypatch, world)
    repos = SimpleNamespace(consultants=_StubConsultants({ORG_B: "active"}))
    user = consultant_user("u-cons", "c@carbontally.test")

    assert await ensure_org_audit_access(user, repos, ORG_B) is None
    assert world.queried_tables == ["organizations"]


@pytest.mark.asyncio
async def test_f2_unusable_lifecycle_store_denies_the_consultant(monkeypatch):
    """F-05-R3 fail closed: a store that cannot answer is a denial, never a 500."""
    world = FakeWorld(
        organizations=[_org_row(ORG_B, active=True)], fail=RuntimeError("store down")
    )
    _install_store(monkeypatch, world)
    repos = SimpleNamespace(consultants=_StubConsultants({ORG_B: "active"}))
    user = consultant_user("u-cons", "c@carbontally.test")

    with pytest.raises(HTTPException) as raised:
        await ensure_org_audit_access(user, repos, ORG_B)

    assert raised.value.status_code == 403
    assert raised.value.detail == ORGANIZATION_SUSPENDED_DETAIL



# ===========================================================================
# F1 — emissions: the record-level exact-tenant ownership rule
# ===========================================================================
def test_f1_verify_refuses_a_cross_tenant_record_and_writes_nothing(monkeypatch):
    """``POST /api/emissions/verify`` writes through the service-role client.

    The five F1 handlers are covered by the D-7 route matrix; this pins the
    record-level rule ``/verify`` needs ON TOP of the organisation guard: a
    record id owned by another tenant is refused outright (403), not counted as
    a per-record failure, and nothing of another tenant's is written.
    """
    from routes import emissions as module

    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A)],
        emissions_logs=[{"id": "rec-b", "organization_id": ORG_B}],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = client.post("/api/emissions/verify", json=["rec-b"])

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "You don't have permission to verify this record"
    assert world.writes == []


def test_f1_verify_own_tenant_record_still_verifies(monkeypatch):
    """No over-blocking: the same handler keeps verifying the caller's records."""
    from routes import emissions as module

    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A)],
        emissions_logs=[{"id": "rec-a", "organization_id": ORG_A}],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = client.post("/api/emissions/verify", json=["rec-a"])

    assert response.status_code == 200, response.text
    assert response.json()["data"]["verified"] == 1
    assert [write[0] for write in world.writes] == ["emissions_logs"]


# ===========================================================================
# F3 — document reviews: the tenant boundary the handler never applied
# ===========================================================================
def test_f3_document_reviews_refuses_a_foreign_tenants_document(monkeypatch):
    """Before F3 this handler read ``customer_review_log`` for ANY file id."""
    from routes import document_activity as module

    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A), _org_row(ORG_B)],
        organization_files=[{"id": "file-b", "organization_id": ORG_B}],
        customer_review_log=[
            {"id": "rev-1", "file_id": "file-b", "status": "approved"}
        ],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = client.get("/api/documents/file-b/reviews")

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not authorized to view this document"
    # The foreign tenant's review log is never read — the membership lookup for
    # the DOCUMENT's organisation already denied.
    assert "customer_review_log" not in world.queried_tables


def test_f3_document_reviews_own_tenant_still_returns_the_review_log(monkeypatch):
    """No over-blocking: a member of the document's organisation keeps access."""
    from routes import document_activity as module

    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A)],
        organization_files=[{"id": "file-a", "organization_id": ORG_A}],
        customer_review_log=[
            {"id": "rev-1", "file_id": "file-a", "status": "approved"}
        ],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = client.get("/api/documents/file-a/reviews")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["total"] == 1
    assert "customer_review_log" in world.queried_tables

