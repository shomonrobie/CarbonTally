"""D-7 Decision B — organisation suspension / reactivation, tenant-isolated.

Approved decision (D-7, "Decision B"): *organisation* suspension is enforced by
the organisation-scoped **guards**, not by authentication. ``organizations.
is_active`` is the single lifecycle flag; while it is ``false`` every
organisation-scoped route denies (owner, admin, consultant, member, viewer) and
NO tenant data is read or written, while

* authentication itself keeps working (``get_current_user`` still returns a
  principal, so ``/auth/status`` and ``/auth/me`` can show the suspension),
* CarbonTally INTERNAL staff keep operational access (support / re-enable),
* re-enable is an ordinary admin action
  (``routes.admin.bulk.bulk_update_organization_status``) that moves the same
  flag the guards read.

Frozen properties this suite pins (each mirrors the F-05-R1 assertion style —
no Supabase, no network, and the DB-visible effects are asserted through the
fake's recorded queries):

1. The decision is taken ONCE, on the principal
   (``AuthUser.organization_is_active``), so the own-tenant path adds **zero**
   database round trips (``world.queries == []``).
2. A foreign organisation's lifecycle is read only AFTER the caller's own role
   has been established, and only when the caller actually has a role there —
   a denied caller never triggers a cross-tenant lifecycle read.
3. The denial is uniform wherever the caller holds a role in the named tenant:
   HTTP 403 with ``ORGANIZATION_SUSPENDED_DETAIL``, the same message for every
   such guard and every role, and never an organisation id (no existence
   disclosure). A caller with NO role in the named tenant keeps the historical
   cross-tenant denials — the organisation-admin guard never swaps its own
   message for the lifecycle one, so another tenant's suspension is not
   disclosed to it either.
4. Membership activation and organisation activation are independent: an
   inactive membership on an ACTIVE organisation keeps its historical
   "Organization member access required" decision.
5. The guards refuse BEFORE the handler, so the handler's tables stay untouched
   (``world.handler_tables == []``) — asserted over real routers as well.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

import auth
from auth import (
    ORGANIZATION_SUSPENDED_DETAIL,
    AuthUser,
    is_organization_active,
    read_organization_active_state,
    require_admin,
    require_auth,
    require_org_access,
    require_org_admin,
    require_org_member,
)
from tests.unit.api.fakes import (
    member_user,
    org_admin_user,
    org_owner_user,
    org_viewer_user,
    staff_user,
)

ORG_A = "org-a"
ORG_B = "org-b"

#: Tables the ORGANISATION GUARDS themselves read. A D-7 denial must never touch
#: anything else: ``handler_tables`` is the DB-visible proof that no
#: organisation-scoped data was reached.
_GUARD_TABLES = frozenset({"organization_members", "organizations"})

# ===========================================================================
# In-memory service-role Supabase fake (guard store + handler data store)
# ===========================================================================
class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal supabase-py query builder: select/eq/limit/update/insert."""

    def __init__(self, world: "FakeWorld", table: str):
        self.world = world
        self.table = table
        self.filters: list = []
        self.payload: Optional[dict] = None
        self.op: Optional[str] = None
        self.single = False

    def select(self, *cols):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def in_(self, key, values):
        """supabase-py ``.in_(key, [...])`` — used by the F1 emissions handlers.

        Recorded as a TUPLE so ``execute`` can tell a set-membership test (``in``)
        from an equality test (``eq``) on the same column.
        """
        self.filters.append((key, tuple(values)))
        return self

    def gte(self, key, value):
        return self

    def lte(self, key, value):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def limit(self, count):
        return self

    def maybe_single(self):
        """supabase-py: ``maybe_single()`` yields ONE row (a dict) or ``None``."""
        self.single = True
        self.world.single_used = True
        return self

    def update(self, payload):
        self.payload = dict(payload)
        self.op = "update"
        return self

    def insert(self, payload):
        self.payload = dict(payload)
        self.op = "insert"
        return self

    def delete(self):
        return self

    def execute(self):
        self.world.queries.append((self.table, tuple(self.filters)))
        if self.world.fail is not None:
            raise self.world.fail
        rows = list(self.world.tables.get(self.table, []))
        for key, value in self.filters:
            if isinstance(value, tuple):
                # ``.in_(key, [...])`` — set membership, not equality.
                rows = [r for r in rows if r.get(key) in value]
            else:
                rows = [r for r in rows if r.get(key) == value]
        if self.op == "update":
            # supabase-py returns the updated rows; an unmatched id returns [].
            for row in rows:
                row.update(self.payload or {})
            self.world.writes.append((self.table, self.op, dict(self.payload or {})))
            return _Result(rows)
        if self.op == "insert":
            self.world.tables.setdefault(self.table, []).append(self.payload)
            self.world.writes.append((self.table, self.op, dict(self.payload or {})))
            return _Result([self.payload])
        if self.single:
            # supabase-py contract: ``maybe_single()`` returns a dict or None.
            return _Result(rows[0] if rows else None)
        return _Result(rows)


class FakeWorld:
    """A fake ``supabase`` client: guard store (membership + organisation)."""

    def __init__(
        self,
        membership_rows=None,
        fail: Optional[Exception] = None,
        user: Optional[tuple] = None,
        **tables: Any,
    ):
        self.tables = {
            "organization_members": list(membership_rows or []),
            "organizations": [],
            "activity_logs": [],
            **tables,
        }
        self.fail = fail
        self.queries: list = []
        self.writes: list = []
        self.single_used = False
        # ``supabase.auth.get_user`` shim — only the ``get_current_user`` test
        # needs it (every other test bypasses authentication deliberately).
        self._user = user
        self.auth = self

    def get_user(self, token):
        if self._user is None:
            return None
        user_id, email = self._user
        return SimpleNamespace(
            user=SimpleNamespace(id=user_id, email=email, user_metadata={})
        )

    def from_(self, table):
        return _Query(self, table)

    @property
    def queried_tables(self):
        return sorted({table for table, _ in self.queries})

    @property
    def handler_tables(self):
        """Tables read by a route HANDLER (never by the auth guards)."""
        return sorted(
            {table for table, _ in self.queries if table not in _GUARD_TABLES}
        )

    def org_row(self, org_id: str):
        for row in self.tables["organizations"]:
            if row.get("id") == org_id:
                return row
        raise AssertionError(f"no organisation row for {org_id} in the fake store")


def _membership(user_id: str, org_id: str, role: str = "member", active: bool = True):
    return {
        "user_id": user_id,
        "organization_id": org_id,
        "role": role,
        "is_active": active,
    }


def _org_row(org_id: str, active: bool = True, name: Optional[str] = None):
    """An ``organizations`` row as the D-7 lifecycle read sees it."""
    return {"id": org_id, "name": name or org_id.upper(), "is_active": active}


# ===========================================================================
# Harness helpers
# ===========================================================================
def _request(**path_params):
    """A stand-in for the injected ``Request`` (only ``path_params`` is read)."""
    return SimpleNamespace(path_params=dict(path_params))


def _install_store(monkeypatch, world: FakeWorld) -> None:
    """Point the guard layer's service-role client at the fake store."""
    monkeypatch.setattr(auth, "get_supabase_client", lambda: world)


def _with_org_state(principal: AuthUser, active: bool) -> AuthUser:
    """The same principal with the D-7 lifecycle state stamped by the resolver.

    ``get_current_user`` stamps ``organization_is_active`` exactly once, from
    ``organizations.is_active``; this mirrors that stamping for principals the
    tests build by hand.
    """
    clone = principal.model_copy(deep=True)
    clone.organization_is_active = bool(active)
    return clone


def _suspended(principal: AuthUser) -> AuthUser:
    return _with_org_state(principal, False)


async def _member_guard(user: AuthUser, path_params):
    checker = require_org_member()
    request = _request(**path_params) if path_params is not None else None
    return await checker(current_user=user, request=request)


async def _admin_guard(user: AuthUser, path_params):
    checker = require_org_admin()
    request = _request(**path_params) if path_params is not None else None
    return await checker(current_user=user, request=request)


async def _access_guard(user: AuthUser, org_id: Optional[str]):
    checker = require_org_access(org_id)
    return await checker(current_user=user)


def _denial(coro_factory) -> HTTPException:
    """Run ``coro_factory()`` and return the HTTPException it must raise."""
    try:
        asyncio.run(coro_factory())
    except HTTPException as exc:
        return exc
    raise AssertionError("expected HTTPException — the guard allowed the call")


def _assert_suspended_denial(exc: HTTPException) -> None:
    """The uniform D-7 denial: 403, one message, no existence disclosure."""
    assert exc.status_code == 403, exc.detail
    assert exc.detail == ORGANIZATION_SUSPENDED_DETAIL
    assert ORG_A not in str(exc.detail) and ORG_B not in str(exc.detail)


def _module_app(monkeypatch, module, world: FakeWorld, user: AuthUser) -> FastAPI:
    """A standalone app over a REAL router, the REAL guards, DB-free (D-7)."""
    _install_store(monkeypatch, world)
    if hasattr(module, "get_supabase_client"):
        monkeypatch.setattr(module, "get_supabase_client", lambda: world)
    app = FastAPI()
    app.include_router(module.router)

    async def _override():
        return user

    app.dependency_overrides[auth.get_current_user] = _override
    return app


# ===========================================================================
# Test 1 — an ACTIVE organisation keeps the frozen behaviour (no over-blocking)
# ===========================================================================
@pytest.mark.asyncio
async def test_1_active_org_member_keeps_access_query_free(monkeypatch):
    """D-7 must be invisible for an active tenant — and cost no extra query."""
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    assert user.organization_is_active is True  # default = active
    assert await _member_guard(user, {"org_id": ORG_A}) is user
    assert await _member_guard(user, None) is user
    assert await _access_guard(user, ORG_A) is user
    # The lifecycle decision travels on the principal: the own-tenant path
    # performs no store round trip at all (F-05-R1's zero-query property holds).
    assert world.queries == []


@pytest.mark.asyncio
async def test_1b_active_org_admin_keeps_admin_authority_query_free(monkeypatch):
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    _install_store(monkeypatch, world)
    for user in (
        org_admin_user(ORG_A, "u-admin", "a@carbontally.test"),
        org_owner_user(ORG_A, "u-admin", "o@carbontally.test"),
    ):
        assert await _admin_guard(user, {"org_id": ORG_A}) is user
    assert world.queries == []


# ===========================================================================
# Test 2 — a SUSPENDED organisation denies every role, on every org guard
# ===========================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "factory,role",
    [
        (member_user, "member"),
        (org_viewer_user, "viewer"),
        (org_admin_user, "admin"),
        (org_owner_user, "owner"),
    ],
)
async def test_2_suspended_org_denies_every_role_on_the_member_guard(
    monkeypatch, factory, role
):
    """Owner/admin/consultant/member/viewer are all denied while suspended."""
    world = FakeWorld(
        [_membership("u-x", ORG_A, role)], organizations=[_org_row(ORG_A, active=False)]
    )
    _install_store(monkeypatch, world)
    user = _suspended(factory(ORG_A, "u-x", "x@carbontally.test"))

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_A})
    _assert_suspended_denial(exc.value)

    # ... and with no organisation in the path (own-tenant routes) too.
    with pytest.raises(HTTPException) as exc2:
        await _member_guard(user, None)
    _assert_suspended_denial(exc2.value)

    # Token-derived decision: the denial is taken before touching the store.
    assert world.queries == []
    assert world.handler_tables == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "factory,role", [(org_admin_user, "admin"), (org_owner_user, "owner")]
)
async def test_2b_suspended_org_strips_admin_authority(monkeypatch, factory, role):
    """No one administers a suspended tenant — owner/admin included."""
    world = FakeWorld(
        [_membership("u-x", ORG_A, role)], organizations=[_org_row(ORG_A, active=False)]
    )
    _install_store(monkeypatch, world)
    user = _suspended(factory(ORG_A, "u-x", "x@carbontally.test"))

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(user, {"org_id": ORG_A})
    _assert_suspended_denial(exc.value)
    assert world.queries == []


# ===========================================================================
# Test 3 — ``require_org_access`` (org-scoped analytics/upload surfaces)
# ===========================================================================
@pytest.mark.asyncio
async def test_3_require_org_access_denies_suspended_own_org_query_free(monkeypatch):
    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A, active=False)],
    )
    _install_store(monkeypatch, world)
    user = _suspended(member_user(ORG_A, "u-member", "m@carbontally.test"))

    with pytest.raises(HTTPException) as exc:
        await _access_guard(user, ORG_A)
    _assert_suspended_denial(exc.value)
    assert world.queries == []


@pytest.mark.asyncio
async def test_3b_require_org_access_keeps_its_tenant_isolation_message(monkeypatch):
    """A foreign organisation keeps the historical F-05-R1 decision."""
    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A, active=True), _org_row(ORG_B, active=True)],
    )
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _access_guard(user, ORG_B)
    assert exc.value.status_code == 403
    assert exc.value.detail == "You don't have access to this organization's data"
    assert world.queries == []


# ===========================================================================
# Test 4 — internal CarbonTally staff keep operational access (support/re-enable)
# ===========================================================================
@pytest.mark.asyncio
async def test_4_internal_staff_keep_access_to_a_suspended_tenant(monkeypatch):
    """Suspension must not lock CarbonTally out of its own support tooling."""
    world = FakeWorld(organizations=[_org_row(ORG_A, active=False)])
    _install_store(monkeypatch, world)
    sysadmin = staff_user("u-sysadmin", role_name="admin")
    assert sysadmin.is_internal_staff and not sysadmin.organization_id

    # The org-admin guard returns for an internal admin before the D-7 check.
    assert await _admin_guard(sysadmin, {"org_id": ORG_A}) is sysadmin
    assert await _access_guard(sysadmin, ORG_A) is sysadmin
    # The foreign organisation's lifecycle is not even read for internal staff.
    assert world.queries == []

    # The global admin authorizer (the re-enable path) is untouched by D-7.
    checker = require_admin()
    assert await checker(current_user=sysadmin) is sysadmin


@pytest.mark.asyncio
async def test_4b_processing_entity_staff_gain_nothing_from_the_suspension(monkeypatch):
    """D20 scope-first still governs: entity staff are not org members."""
    from tests.unit.api.fakes import entity_operator_user

    world = FakeWorld(
        [_membership("u-entity-op", ORG_A, "member")],
        organizations=[_org_row(ORG_A, active=False)],
    )
    _install_store(monkeypatch, world)
    entity_op = entity_operator_user("entity-1")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(entity_op, {"org_id": ORG_A})
    assert exc.value.status_code == 403
    assert exc.value.detail == "Organization member access required"
    assert world.queries == []


# ===========================================================================
# Test 5 — HTTP level over REAL routers: the guard refuses before the handler
# ===========================================================================
#: Real organisation-scoped routes (from the F-05-R1 frozen surface), across
#: several routers and several organisation path spellings. Each entry is
#: (module, method, url template, json body, role the route's OWN guard needs).
_ORG_SCOPED_ROUTES = [
    pytest.param(
        "routes.organizations.exports", "GET", "/api/organizations/{org}/exports",
        None, "member", id="exports-list",
    ),
    pytest.param(
        "routes.organizations.exports", "POST",
        "/api/organizations/{org}/exports/exports/emissions", {"format": "csv"},
        "member", id="exports-emissions",
    ),
    pytest.param(
        "routes.organizations.exports", "DELETE",
        "/api/organizations/{org}/exports/exp-1", None, "admin", id="exports-delete",
    ),
    pytest.param(
        "routes.organizations.data", "GET",
        "/api/organizations/data/{org}/emissions-data", None, "member", id="data-emissions",
    ),
    pytest.param(
        "routes.organizations.assets", "GET",
        "/api/organizations/{org}/facilities", None, "member", id="facilities-list",
    ),
    pytest.param(
        "routes.organizations.metadata", "GET",
        "/api/organizations/{org}/metadata/industry", None, "member", id="metadata-industry",
    ),
    pytest.param(
        "routes.organizations.files", "GET",
        "/api/organizations/files/{org}/files/archived", None, "admin", id="files-archived",
    ),
    # F1 (D-7) — emissions handlers that were gated only by ``require_auth()``.
    # None names an organisation in the path: the caller's OWN tenant is the
    # decision, so a suspended caller is refused before the handler runs.
    # ``routes/emissions.py`` carries ``APIRouter(prefix="/api")`` and main.py
    # mounts it as-is, so these are the served paths.
    pytest.param(
        "routes.emissions", "PUT", "/api/emissions/rec-1",
        {"raw_quantity": 1.0}, "member", id="f1-emissions-update",
    ),
    pytest.param(
        "routes.emissions", "POST", "/api/emissions/bulk",
        {"emissions": []}, "member", id="f1-emissions-bulk",
    ),
    pytest.param(
        "routes.emissions", "GET", "/api/emissions/stats",
        None, "member", id="f1-emissions-stats",
    ),
    pytest.param(
        "routes.emissions", "GET", "/api/emissions/export",
        None, "member", id="f1-emissions-export",
    ),
    pytest.param(
        "routes.emissions", "POST", "/api/emissions/verify",
        ["rec-1"], "member", id="f1-emissions-verify",
    ),
    # F3 (D-7) — document activity handlers that were gated only by
    # ``require_auth()`` (``/{file_id}/reviews`` additionally had no tenant
    # check at all at the time).
    pytest.param(
        "routes.document_activity", "GET", "/api/documents/file-1/activity",
        None, "member", id="f3-document-activity",
    ),
    pytest.param(
        "routes.document_activity", "GET", "/api/documents/file-1/reviews",
        None, "member", id="f3-document-reviews",
    ),
    pytest.param(
        "routes.document_activity", "POST", "/api/documents/file-1/review/response",
        {"status": "approved"}, "member", id="f3-review-response",
    ),
]


def _route_principal(required_role: str, org_id: str = ORG_A):
    """The principal + membership row a route with ``required_role`` needs."""
    if required_role == "admin":
        return (
            org_admin_user(org_id, "u-admin", "a@carbontally.test"),
            _membership("u-admin", org_id, "admin"),
        )
    return (
        member_user(org_id, "u-member", "m@carbontally.test"),
        _membership("u-member", org_id, "member"),
    )


def _call(client: TestClient, method: str, url: str, payload):
    if method == "GET":
        return client.get(url)
    if method == "POST":
        return client.post(url, json=payload or {})
    if method == "PUT":
        return client.put(url, json=payload or {})
    if method == "DELETE":
        return client.delete(url)
    raise AssertionError(f"unsupported method {method}")


@pytest.mark.parametrize(
    "module_path,method,url_template,payload,required_role", _ORG_SCOPED_ROUTES
)
def test_5_suspended_tenant_is_refused_before_any_handler_runs(
    monkeypatch, module_path, method, url_template, payload, required_role
):
    """Every real org-scoped route denies an INACTIVE tenant's member.

    The caller is deliberately a plain MEMBER even on the admin-gated routes:
    the lifecycle denial must precede the admission test (which role the route
    wants) as well as the handler, so the outcome is identical for owner, admin,
    consultant, member and viewer.
    """
    import importlib

    module = importlib.import_module(module_path)
    world = FakeWorld(
        [
            _membership("u-member", ORG_A, "member"),
            _membership("u-admin", ORG_A, "admin"),
        ],
        organizations=[_org_row(ORG_A, active=False)],
    )
    user = _suspended(member_user(ORG_A, "u-member", "m@carbontally.test"))
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = _call(client, method, url_template.format(org=ORG_A), payload)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == ORGANIZATION_SUSPENDED_DETAIL
    # The denial is the DB-visible proof: no handler table was ever read, so no
    # tenant data could be returned to (or written by) a suspended tenant.
    assert world.handler_tables == []


@pytest.mark.parametrize(
    "module_path,method,url_template,payload,required_role", _ORG_SCOPED_ROUTES
)
def test_6_active_tenant_keeps_reaching_the_same_routes(
    monkeypatch, module_path, method, url_template, payload, required_role
):
    """Same routes, ACTIVE tenant: the D-7 denial is lifecycle-specific only."""
    import importlib

    module = importlib.import_module(module_path)
    user, membership = _route_principal(required_role)
    world = FakeWorld([membership], organizations=[_org_row(ORG_A, active=True)])
    app = _module_app(monkeypatch, module, world, user)

    with TestClient(app) as client:
        response = _call(client, method, url_template.format(org=ORG_A), payload)

    # An ACTIVE tenant gets no lifecycle denial, and the suspended message never
    # appears. Member-level routes must additionally clear their own 403 (the
    # admin-gated ones are judged by their own guard, which is not D-7's claim).
    assert ORGANIZATION_SUSPENDED_DETAIL not in response.text, response.text
    if required_role == "member":
        assert response.status_code != 403, response.text


def test_6b_active_tenant_org_scoped_export_still_succeeds(monkeypatch):
    """The F-05-R1 route that motivated the suite keeps its 200 behaviour."""
    from routes.organizations import exports as exports_module

    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A, active=True)],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, exports_module, world, user)

    with TestClient(app) as client:
        response = client.post(
            f"/api/organizations/{ORG_A}/exports/exports/emissions",
            json={"format": "csv"},
        )

    assert response.status_code == 200, response.text
    assert "emissions_logs" in world.queried_tables


# ===========================================================================
# Test 7 — an admin suspension/reactivation moves the flag the guards read
# ===========================================================================
@pytest.mark.asyncio
async def test_7_admin_suspend_then_reactivate_moves_the_lifecycle_flag(monkeypatch):
    """The D-7 flip is wired into the real admin status handler."""
    from routes.admin import bulk as bulk_module

    world = FakeWorld(organizations=[_org_row(ORG_A, active=True, name="Acme")])
    _install_store(monkeypatch, world)
    monkeypatch.setattr(bulk_module, "get_supabase_client", lambda: world)
    admin = staff_user("u-sysadmin", role_name="admin")

    suspended = await bulk_module.bulk_update_organization_status(
        bulk_module.BulkOrganizationStatusUpdate(
            organization_ids=[ORG_A], status="suspended", reason="non-payment"
        ),
        current_user=admin,
    )
    assert suspended["success"] is True
    assert suspended["data"]["success_count"] == 1
    assert suspended["data"]["errors"] == []
    # The admin's action moved the lifecycle flag AND the audited status.
    assert suspended["data"]["data"][0]["is_active"] is False
    assert suspended["data"]["data"][0]["name"] == "Acme"
    assert world.org_row(ORG_A)["is_active"] is False
    assert world.org_row(ORG_A)["subscription_status"] == "suspended"
    assert any(table == "activity_logs" for table, _op, _p in world.writes)

    # The store is now the single source of truth the guards read.
    assert is_organization_active(ORG_A) is False
    owner = org_owner_user(ORG_A, "u-owner", "o@carbontally.test")
    principal = _with_org_state(owner, is_organization_active(ORG_A))
    assert principal.organization_is_active is False
    assert await _admin_guard(admin, {"org_id": ORG_A}) is admin  # support unblocked
    with pytest.raises(HTTPException) as exc:
        await _member_guard(principal, {"org_id": ORG_A})
    _assert_suspended_denial(exc.value)

    # Re-enable is the same handler: active → is_active = true.
    reactivated = await bulk_module.bulk_update_organization_status(
        bulk_module.BulkOrganizationStatusUpdate(organization_ids=[ORG_A], status="active"),
        current_user=admin,
    )
    assert reactivated["data"]["success_count"] == 1
    assert reactivated["data"]["data"][0]["is_active"] is True
    assert world.org_row(ORG_A)["is_active"] is True
    assert is_organization_active(ORG_A) is True

    # Nobody inside the tenant is denied any more (own-tenant path, no query).
    world.queries.clear()
    assert await _member_guard(owner, {"org_id": ORG_A}) is owner
    assert world.queries == []


@pytest.mark.asyncio
@pytest.mark.parametrize("status,expected", [("archived", False), ("active", True)])
async def test_7b_status_map_covers_archived_and_active(monkeypatch, status, expected):
    from routes.admin.bulk import _ORG_STATUS_ACTIVE_STATE

    assert _ORG_STATUS_ACTIVE_STATE["suspended"] is False
    assert _ORG_STATUS_ACTIVE_STATE[status] is expected
    # An unknown status keeps the historical subscription-status-only behaviour
    # rather than guessing a lifecycle.
    assert "deleted" not in _ORG_STATUS_ACTIVE_STATE


# ===========================================================================
# Test 8 — access resumes for the same tenant once the admin reactivates it
# ===========================================================================
@pytest.mark.asyncio
async def test_8_access_resumes_after_reactivation_on_the_same_store(monkeypatch):
    world = FakeWorld(
        [_membership("u-owner", ORG_A, "owner")],
        organizations=[_org_row(ORG_A, active=False)],
    )
    _install_store(monkeypatch, world)
    owner = org_owner_user(ORG_A, "u-owner", "o@carbontally.test")

    def stamped():
        """The principal as the NEXT request would resolve it (fresh token)."""
        return _with_org_state(owner, is_organization_active(ORG_A))

    assert stamped().organization_is_active is False
    with pytest.raises(HTTPException) as exc:
        await _member_guard(stamped(), {"org_id": ORG_A})
    _assert_suspended_denial(exc.value)
    with pytest.raises(HTTPException) as exc2:
        await _admin_guard(stamped(), {"org_id": ORG_A})
    _assert_suspended_denial(exc2.value)

    # The CarbonTally admin re-enables the tenant (same flag the guards read).
    world.org_row(ORG_A)["is_active"] = True

    # The NEXT request resolves a fresh principal from the same store…
    reactivated = stamped()
    assert reactivated.organization_is_active is True
    world.queries.clear()
    # …and full recovery is still query-free on the own-tenant path.
    assert await _member_guard(reactivated, {"org_id": ORG_A}) is reactivated
    assert await _admin_guard(reactivated, {"org_id": ORG_A}) is reactivated
    assert world.queries == []


# ===========================================================================
# Test 9 — membership activation vs organisation activation are independent
# ===========================================================================
@pytest.mark.asyncio
async def test_9a_inactive_membership_on_an_active_org_keeps_its_old_decision(
    monkeypatch,
):
    """D-7 must not turn the membership decision into a lifecycle one."""
    world = FakeWorld(organizations=[_org_row(ORG_A, active=True)])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    user.is_org_member = False  # membership de-activated by an org admin

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_A})
    assert exc.value.status_code == 403
    assert exc.value.detail == "Organization member access required"
    # The organisation lifecycle was never consulted for a non-member.
    assert world.queries == []


@pytest.mark.asyncio
async def test_9b_active_membership_in_a_suspended_foreign_tenant_is_denied(
    monkeypatch,
):
    """Cross-tenant hole: an ACTIVE row in an INACTIVE tenant is no authority."""
    world = FakeWorld(
        [_membership("u-both", ORG_B, "owner")],
        organizations=[_org_row(ORG_B, active=False)],
    )
    _install_store(monkeypatch, world)
    caller = member_user(ORG_A, "u-both", "b@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(caller, {"org_id": ORG_B})
    _assert_suspended_denial(exc.value)
    assert world.handler_tables == []


@pytest.mark.asyncio
async def test_9c_unknown_foreign_org_state_keeps_the_frozen_f05_decision(
    monkeypatch,
):
    """No new blanket denial: an unexposed foreign row leaves F-05-R1 standing."""
    world = FakeWorld([_membership("u-both", ORG_B, "member")])
    _install_store(monkeypatch, world)
    caller = member_user(ORG_A, "u-both", "b@carbontally.test")

    assert await _member_guard(caller, {"org_id": ORG_B}) is caller
    # Only "explicitly inactive" denies; the foreign state was read once.
    assert world.queries == [
        ("organization_members", (("user_id", "u-both"), ("organization_id", ORG_B), ("is_active", True))),
        ("organizations", (("id", ORG_B),)),
    ]


# ===========================================================================
# Test 10 — the foreign lifecycle read is deferred until authority is proven
# ===========================================================================
@pytest.mark.asyncio
async def test_10a_foreign_lifecycle_is_read_only_after_the_role_is_established(
    monkeypatch,
):
    """Ordering proof: membership authority first, lifecycle second — never both
    up front, and never for a caller who has no authority there at all."""
    world = FakeWorld(
        [_membership("u-admin", ORG_B, "admin")],
        organizations=[_org_row(ORG_B, active=False)],
    )
    _install_store(monkeypatch, world)
    foreign_admin = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(foreign_admin, {"org_id": ORG_B})
    assert exc.value.status_code == 403
    # The admin guard answers with its own historical denial: an outsider is
    # never told WHY another tenant's organisation is unusable (no lifecycle
    # disclosure across tenants). The member guard, which reaches D-7 only after
    # membership authority is established, uses ORGANIZATION_SUSPENDED_DETAIL
    # (test_9b).
    assert exc.value.detail == "Organization admin privileges required"
    assert _organization_inactive_was_read_after_the_role(world)
    assert world.handler_tables == []


def _organization_inactive_was_read_after_the_role(world: FakeWorld) -> bool:
    """The foreign lifecycle read happens exactly once, after the role read."""
    tables = [table for table, _ in world.queries]
    return tables == ["organization_members", "organizations"]


@pytest.mark.asyncio
async def test_10b_a_denied_caller_never_triggers_a_foreign_lifecycle_read(
    monkeypatch,
):
    """No cross-tenant lifecycle probe, and no extra DB call, for non-authority."""
    world = FakeWorld(organizations=[_org_row(ORG_B, active=False)])
    _install_store(monkeypatch, world)
    foreign_member = member_user(ORG_A, "u-member", "m@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(foreign_member, {"org_id": ORG_B})
    assert exc.value.status_code == 403
    assert exc.value.detail == "Organization admin privileges required"
    assert [table for table, _ in world.queries] == ["organization_members"]


@pytest.mark.asyncio
async def test_10c_an_authority_shaped_outsider_still_learns_nothing(monkeypatch):
    """An owner/admin of ANOTHER tenant is denied without a lifecycle probe.

    This is the most dangerous probe shape: the caller already holds
    ``org_owner``/``org_admin`` names, so a naive implementation would read the
    foreign lifecycle *before* checking whether they have any role there.
    """
    world = FakeWorld(organizations=[_org_row(ORG_B, active=False)])
    _install_store(monkeypatch, world)

    for caller in (
        org_admin_user(ORG_A, "u-admin", "a@carbontally.test"),
        org_owner_user(ORG_A, "u-owner", "o@carbontally.test"),
    ):
        world.queries.clear()
        with pytest.raises(HTTPException) as exc:
            await _admin_guard(caller, {"org_id": ORG_B})
        assert exc.value.status_code == 403
        assert exc.value.detail == "Organization admin privileges required"
        assert ORGANIZATION_SUSPENDED_DETAIL != exc.value.detail
        # Only the caller's OWN membership row was consulted: the foreign
        # organisation's lifecycle was never read.
        assert world.queried_tables == ["organization_members"]


# ===========================================================================
# Test 11 — the resolver stamps the lifecycle state on the principal
# ===========================================================================
def _resolve_principal(monkeypatch, world: FakeWorld, token: str = "token-1") -> AuthUser:
    """Run the REAL ``get_current_user`` against the fake store."""
    _install_store(monkeypatch, world)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return asyncio.run(auth.get_current_user(credentials))


def test_11a_active_organisation_is_stamped_active(monkeypatch):
    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        user=("u-member", "m@carbontally.test"),
        organizations=[_org_row(ORG_A, active=True)],
    )
    principal = _resolve_principal(monkeypatch, world)

    assert principal.organization_id == ORG_A
    assert principal.is_org_member is True
    assert principal.organization_is_active is True
    # The resolver reaches the membership through ``maybe_single()`` (the F-05-R3
    # hazard area); the D-7 lifecycle read is a plain list query.
    assert world.single_used is True

    world.queries.clear()
    assert asyncio.run(_member_guard(principal, {"org_id": ORG_A})) is not None
    assert world.queries == []  # the stamping removed every guard round trip


def test_11b_inactive_organisation_is_stamped_inactive(monkeypatch):
    """The linchpin: without this stamp no guard could fail closed."""
    world = FakeWorld(
        [_membership("u-owner", ORG_A, "owner")],
        user=("u-owner", "o@carbontally.test"),
        organizations=[_org_row(ORG_A, active=False)],
    )
    principal = _resolve_principal(monkeypatch, world)

    assert principal.is_org_member is True
    assert principal.organization_is_active is False

    world.queries.clear()
    _assert_suspended_denial(
        _denial(lambda: _member_guard(principal, {"org_id": ORG_A}))
    )
    assert world.queries == []


@pytest.mark.parametrize(
    "organizations",
    [
        pytest.param([], id="no-organisation-row"),
        pytest.param([{"id": ORG_A, "is_active": None}], id="null-is-active"),
    ],
)
def test_11c_unknown_lifecycle_state_fails_closed(monkeypatch, organizations):
    """``organizations.is_active`` is NOT NULL DEFAULT true: unknown = deny."""
    world = FakeWorld(
        [_membership("u-owner", ORG_A, "owner")],
        user=("u-owner", "o@carbontally.test"),
        organizations=organizations,
    )
    principal = _resolve_principal(monkeypatch, world)

    assert principal.organization_is_active is False
    _assert_suspended_denial(
        _denial(lambda: _member_guard(principal, {"org_id": ORG_A}))
    )


def test_11d_unusable_store_denies_and_never_raises_500(monkeypatch):
    """A store failure is a denial, never an HTTP 500 (fail closed)."""
    world = FakeWorld(
        [_membership("u-owner", ORG_A, "owner")],
        user=("u-owner", "o@carbontally.test"),
        fail=RuntimeError("supabase unavailable"),
    )
    principal = _resolve_principal(monkeypatch, world)

    assert principal.is_org_member is False  # the membership read failed too
    exc = _denial(lambda: _member_guard(principal, {"org_id": ORG_A}))
    assert exc.status_code == 403
    assert exc.detail in (ORGANIZATION_SUSPENDED_DETAIL, "Organization member access required")


# ===========================================================================
# Test 12 — wiring freezes: authentication stays open, body-scope stays guarded
# ===========================================================================
#: Modules that call ``enforce_org_body_scope`` (POD-5 body-scope rule). Every
#: one of them must also carry the organisation guard, or D-7 would be bypassed
#: by a body-named organisation.
_BODY_SCOPE_MODULES = ("report_generator.py", "routes/reports.py", "routes/upload.py")

_BACKEND_ROOT = Path(auth.__file__).resolve().parent


def _backend_sources():
    """Every application Python module (no tests, no virtualenv)."""
    for path in sorted(_BACKEND_ROOT.rglob("*.py")):
        rel = path.relative_to(_BACKEND_ROOT)
        if rel.parts[0] in {"tests", ".venv", "node_modules"} or rel.parts[0].startswith("."):
            continue
        yield rel.as_posix(), path


def test_12a_authentication_is_never_organisation_scoped(monkeypatch):
    """``/auth/status``+``/auth/me`` must keep answering for a suspended tenant."""
    import inspect

    for name in ("get_current_user", "require_auth", "require_admin"):
        src = inspect.getsource(getattr(auth, name))
        assert "ORGANIZATION_SUSPENDED_DETAIL" not in src, name
        assert "_caller_organization_inactive" not in src, name
        assert "_organization_inactive_for_path_org" not in src, name

    # ... and conversely, every organisation-scoped guard raises the D-7 denial
    # itself: one status, one message, whatever role the route asks for.
    for name in (
        "require_org_member",
        "require_org_admin",
        "require_org_access",
        "enforce_org_path_scope",
    ):
        src = inspect.getsource(getattr(auth, name))
        assert "ORGANIZATION_SUSPENDED_DETAIL" in src, name
        assert (
            "_caller_organization_inactive" in src
            or "_organization_inactive_for_path_org" in src
        ), name

    # ``_org_admin_authority`` is the boolean authority predicate the admin guard
    # composes: it DECIDES, it does not raise. The message therefore stays in the
    # guards, which is why an outsider is answered with the historical cross-tenant
    # denial instead of the lifecycle detail (test_10a/test_10c).
    authority_src = inspect.getsource(auth._org_admin_authority)
    assert "_organization_inactive_for_path_org" in authority_src
    assert "ORGANIZATION_SUSPENDED_DETAIL" not in authority_src

    # Behaviour: an authenticated principal of a suspended tenant is still
    # authenticated (that is what makes the suspension visible to the client).
    world = FakeWorld(organizations=[_org_row(ORG_A, active=False)])
    _install_store(monkeypatch, world)
    suspended = _suspended(member_user(ORG_A, "u-member", "m@carbontally.test"))
    assert asyncio.run(require_auth()(current_user=suspended)) is suspended
    assert asyncio.run(require_admin()(current_user=staff_user("u-sysadmin", role_name="admin")))
    assert world.queries == []


def test_12b_every_body_scope_call_site_still_carries_an_org_guard():
    """A new body-scope call site without the guard would silently reopen POD-5."""
    discovered = {
        rel for rel, path in _backend_sources() if "enforce_org_body_scope(" in path.read_text(
            encoding="utf-8", errors="ignore"
        )
    }
    # ``auth.py`` holds the definition; the three routes are the call sites.
    assert discovered == set(_BODY_SCOPE_MODULES) | {"auth.py"}, sorted(discovered)
    for rel in _BODY_SCOPE_MODULES:
        text = (_BACKEND_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        assert "require_org_member()" in text, rel
        assert "enforce_org_body_scope(" in text, rel


# ===========================================================================
# Test 13 — the lifecycle predicate contract (fail closed, no 500)
# ===========================================================================
class _StubClient:
    """A client whose single-table read returns ``data`` (or raises) verbatim."""

    def __init__(self, data=None, error: Optional[Exception] = None):
        self._data = data
        self._error = error
        self.reads: list = []
        self.auth = self

    def from_(self, table):
        self.reads.append(table)
        return self

    def select(self, *cols):
        return self

    def eq(self, *args):
        return self

    def limit(self, *args):
        return self

    def execute(self):
        if self._error is not None:
            raise self._error
        return SimpleNamespace(data=self._data)


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"is_active": True}, True),
        ({"is_active": False}, False),
        ([{"is_active": True}], True),
        ([{"is_active": False}], False),
        ([{"is_active": None}], None),
        ([], None),
        (None, None),
        ("unexpected-shape", None),
    ],
)
def test_13a_lifecycle_read_maps_known_states_and_reports_unknown(
    monkeypatch, data, expected
):
    stub = _StubClient(data)
    monkeypatch.setattr(auth, "get_supabase_client", lambda: stub)
    assert read_organization_active_state(ORG_A) is expected
    assert is_organization_active(ORG_A) is (expected is True)
    # Both call sites read the ONE lifecycle table, exactly once each — no other
    # table is consulted to answer "is this tenant live?".
    assert stub.reads == ["organizations", "organizations"]


def test_13b_an_empty_organisation_id_never_reaches_the_store(monkeypatch):
    stub = _StubClient({"is_active": True}, error=AssertionError("must not read"))
    monkeypatch.setattr(auth, "get_supabase_client", lambda: stub)
    assert read_organization_active_state("") is None
    assert read_organization_active_state(None) is None
    assert is_organization_active("") is False
    assert stub.reads == []


def test_13c_store_failures_fail_closed_and_never_500(monkeypatch):
    monkeypatch.setattr(
        auth, "get_supabase_client", lambda: _StubClient(error=RuntimeError("boom"))
    )
    assert is_organization_active(ORG_A) is False
    with pytest.raises(RuntimeError):  # the raw reader propagates...
        read_organization_active_state(ORG_A)  # ...the policy wrapper denies.

    # An unconfigured store raises HTTPException from the client factory: still a
    # denial, still no 500 for the caller.
    def _unconfigured():
        raise HTTPException(status_code=500, detail="Supabase not configured")

    monkeypatch.setattr(auth, "get_supabase_client", _unconfigured)
    assert is_organization_active(ORG_A) is False
    _assert_suspended_denial(
        _denial(lambda: _member_guard(_suspended(member_user(ORG_A, "u", "u@x.test")), {"org_id": ORG_A}))
    )
