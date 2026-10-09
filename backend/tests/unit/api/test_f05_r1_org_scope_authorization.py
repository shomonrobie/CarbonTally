"""CT-FINAL-01 · F-05-R1 / F-05-R3 — organisation-scope authorization matrix.

The release-blocking defect (F-05-R1): ``require_org_member()`` /
``require_org_admin()`` only proved that the caller was a member of *some*
organisation, while the handler then used the service-role Supabase client
scoped **only** by the organisation id taken from the request PATH. Any
authenticated organisation member could read and write another organisation's
data by changing that path parameter — reproduced on
``POST /api/organizations/{org_id}/exports/exports/emissions``.

F-05-R3 (same surface): the authoritative ``require_org_admin`` fallback used
``maybe_single()``, which raised ``AttributeError`` on ``None`` for a caller
with several memberships (or with no row at all) and surfaced as HTTP 500
instead of a 403 authorization decision.

Every test here is DB-free: the guards run their REAL code
(``backend/auth.py``) against an in-memory ``organization_members`` store, and
the routes are the real routers. Both the ALLOW and the DENY direction is
asserted (AGENTS.md §45).
"""
from __future__ import annotations

import ast
import pathlib
from types import SimpleNamespace
from typing import Optional

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import auth
from auth import (
    get_request_org_scope,
    require_org_admin,
    require_org_member,
)
from tests.unit.api.fakes import (
    member_user,
    org_admin_user,
    org_owner_user,
    org_viewer_user,
    staff_user,
    entity_operator_user,
)

ORG_A = "org-a"
ORG_B = "org-b"


# ---------------------------------------------------------------------------
# In-memory service-role Supabase fake (membership store + handler data store)
# ---------------------------------------------------------------------------
class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal supabase-py query builder: select/eq/limit/execute."""

    def __init__(self, world, table):
        self.world = world
        self.table = table
        self.filters = []

    def select(self, *cols):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
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
        self.world.single_used = True
        return self

    def delete(self):
        return self

    def execute(self):
        self.world.queries.append((self.table, tuple(self.filters)))
        if self.world.fail is not None:
            raise self.world.fail
        rows = list(self.world.tables.get(self.table, []))
        for key, value in self.filters:
            rows = [r for r in rows if r.get(key) == value]
        return _Result(rows)


class FakeWorld:
    """A fake ``supabase`` client holding arbitrary named tables."""

    def __init__(self, membership_rows=None, fail: Optional[Exception] = None, **tables):
        self.tables = {
            "organization_members": list(membership_rows or []),
            "emissions_logs": [],
            "export_history": [],
            **tables,
        }
        self.fail = fail
        self.queries = []
        self.single_used = False

    def from_(self, table):
        return _Query(self, table)

    @property
    def queried_tables(self):
        return sorted({table for table, _ in self.queries})

    @property
    def handler_tables(self):
        """Tables queried by the route HANDLER (not by the auth guard)."""
        return sorted(
            {table for table, _ in self.queries if table != "organization_members"}
        )


def _membership(user_id: str, org_id: str, role: str = "member", active: bool = True) -> dict:
    return {
        "user_id": user_id,
        "organization_id": org_id,
        "role": role,
        "is_active": active,
    }


def _request(**path_params):
    """A stand-in for the injected ``Request`` (only ``path_params`` is read)."""
    return SimpleNamespace(path_params=dict(path_params))


def _install_store(monkeypatch, world: FakeWorld) -> None:
    monkeypatch.setattr(auth, "get_supabase_client", lambda: world)


async def _member_guard(user, path_params):
    checker = require_org_member()
    request = _request(**path_params) if path_params is not None else None
    return await checker(current_user=user, request=request)

async def _admin_guard(user, path_params):
    checker = require_org_admin()
    request = _request(**path_params) if path_params is not None else None
    return await checker(current_user=user, request=request)


# ---------------------------------------------------------------------------
# Case A — cross-tenant read: member of org-a must not reach org-b's path
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_a_member_of_org_a_is_denied_on_org_b_path(monkeypatch):
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403
    assert "access to this organization" in str(exc.value.detail)


# ---------------------------------------------------------------------------
# Case B — the caller's own organisation keeps working (no over-blocking)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_b_member_of_org_a_is_allowed_on_org_a_path(monkeypatch):
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    result = await _member_guard(user, {"org_id": ORG_A})

    assert result is user
    # Own-organisation requests take the token-derived fast path: the guard
    # performs no membership round trip at all.
    assert world.queries == []


# ---------------------------------------------------------------------------
# Case C — a genuine member of several organisations keeps both (DB-verified)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_c_multi_org_member_is_allowed_on_second_org(monkeypatch):
    world = FakeWorld(
        [
            _membership("u-both", ORG_A, "member"),
            _membership("u-both", ORG_B, "member"),
        ]
    )
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-both", "both@carbontally.test")

    result = await _member_guard(user, {"org_id": ORG_B})

    assert result is user
    assert world.queries[0][0] == "organization_members"


# ---------------------------------------------------------------------------
# Case D — an INACTIVE membership in the path organisation is not authority
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_d_inactive_membership_is_denied(monkeypatch):
    world = FakeWorld([_membership("u-inactive", ORG_B, "member", active=False)])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-inactive", "inactive@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Case E — a viewer never gains another tenant's scope
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_e_viewer_of_org_a_is_denied_on_org_b_path(monkeypatch):
    world = FakeWorld([_membership("u-viewer", ORG_A, "viewer")])
    _install_store(monkeypatch, world)
    user = org_viewer_user(ORG_A, "u-viewer", "v@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Case F — Processing Entity staff never reach a customer organisation (D20)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_f_pe_staff_is_denied(monkeypatch):
    world = FakeWorld()
    _install_store(monkeypatch, world)
    user = entity_operator_user("entity-1")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_A})

    assert exc.value.status_code == 403
    assert "member access required" in str(exc.value.detail)


# ---------------------------------------------------------------------------
# Case G — CarbonTally internal staff keep approved cross-tenant operations
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_g_internal_staff_member_keeps_operational_access(monkeypatch):
    world = FakeWorld([_membership("u-ops", ORG_A, "member")])
    _install_store(monkeypatch, world)
    user = staff_user("u-ops")
    user.organization_id = ORG_A
    user.is_org_member = True

    assert user.is_internal_staff is True
    result = await _member_guard(user, {"org_id": ORG_B})
    assert result is user


# ---------------------------------------------------------------------------
# F-05-R3 — the membership store must never turn a denial into an HTTP 500
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_case_h_unconfigured_store_denies_with_403_not_500(monkeypatch):
    world = FakeWorld(
        fail=HTTPException(status_code=500, detail="Supabase configuration missing")
    )
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_case_i_store_failure_denies_with_403_not_500(monkeypatch):
    world = FakeWorld(fail=RuntimeError("connection reset by peer"))
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _member_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403
    assert "connection reset" not in str(exc.value.detail)


@pytest.mark.asyncio
async def test_case_j_multi_membership_admin_lookup_is_403_not_500(monkeypatch):
    """The exact F-05-R3 shape: several membership rows, none of them admin."""
    world = FakeWorld(
        [
            _membership("u-multi", ORG_A, "member"),
            _membership("u-multi", ORG_B, "member"),
        ]
    )
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-multi", "multi@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403
    # ``maybe_single`` must be gone from this path — that is what produced 500s.
    assert world.single_used is False


@pytest.mark.asyncio
async def test_case_k_unauthenticated_is_401(monkeypatch):
    _install_store(monkeypatch, FakeWorld())
    with pytest.raises(HTTPException) as exc:
        await _member_guard(None, {"org_id": ORG_A})
    assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# Route shape — no organisation in the path keeps the historical behaviour,
# and direct (unit-test) calls without an injected Request stay callable.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_path_org_keeps_historical_membership_only_behaviour(monkeypatch):
    _install_store(monkeypatch, FakeWorld())
    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    assert await _member_guard(user, {}) is user
    assert await _member_guard(user, None) is user


def test_request_org_scope_reads_all_path_parameter_spellings():
    assert get_request_org_scope(_request(organization_id="o1")) == ("o1",)
    assert get_request_org_scope(_request(org_id="o2")) == ("o2",)
    assert get_request_org_scope(_request(organisation_id="o3")) == ("o3",)
    assert get_request_org_scope(_request(org_id="")) == ()
    assert get_request_org_scope(_request(other="x")) == ()
    assert get_request_org_scope(None) == ()


def test_request_org_scope_deduplicates():
    assert get_request_org_scope(_request(org_id="o1", organization_id="o1")) == ("o1",)


def test_real_routes_inject_the_request_into_the_org_guards():
    """F-05-R1 depends on FastAPI injecting ``Request`` into the guard.

    If the ``request`` parameter were removed or renamed, the path-scope check
    would silently stop running — the exact failure mode this suite exists to
    catch (verified against FastAPI 0.141.1).
    """


# ---------------------------------------------------------------------------
# HTTP level — the REAL router, the REAL guards (the reported F-05-R1 route)
# ---------------------------------------------------------------------------
def _exports_app(monkeypatch, user, world):
    """Standalone app over the real legacy exports router (hermetic, DB-free)."""
    from routes.organizations import exports as exports_module

    _install_store(monkeypatch, world)
    monkeypatch.setattr(exports_module, "get_supabase_client", lambda: world)

    app = FastAPI()
    app.include_router(exports_module.router)

    async def _override():
        return user

    app.dependency_overrides[auth.get_current_user] = _override
    return app


def test_http_member_of_org_a_cannot_export_org_b_emissions(monkeypatch):
    """F-05-R1 reproduction: the exact route from the release-blocking finding.

    Before the fix this returned organisation B's emissions data to a member of
    organisation A. Now the guard refuses before the handler (and therefore
    before any service-role read) runs.
    """
    world = FakeWorld(
        [
            _membership("u-member", ORG_A, "member"),
            {"id": "log-b", "organization_id": ORG_B, "quantity": 10},
        ]
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.post(
            f"/api/organizations/{ORG_B}/exports/exports/emissions",
            json={"format": "csv"},
        )

    assert response.status_code == 403, response.text
    # The cross-tenant read never happened: only the guard's own membership
    # lookup ran — the handler's data tables were never touched.
    assert world.handler_tables == []


def test_http_member_of_org_a_can_export_own_org(monkeypatch):
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.post(
            f"/api/organizations/{ORG_A}/exports/exports/emissions",
            json={"format": "csv"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["record_count"] == 0
    assert "emissions_logs" in world.queried_tables


def test_http_viewer_of_org_a_cannot_list_org_b_exports(monkeypatch):
    world = FakeWorld([_membership("u-viewer", ORG_A, "viewer")])
    user = org_viewer_user(ORG_A, "u-viewer", "v@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.get(f"/api/organizations/{ORG_B}/exports")

    assert response.status_code == 403, response.text
    assert world.handler_tables == []


def test_http_viewer_of_org_a_can_list_own_org_exports(monkeypatch):
    world = FakeWorld([_membership("u-viewer", ORG_A, "viewer")])
    user = org_viewer_user(ORG_A, "u-viewer", "v@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.get(f"/api/organizations/{ORG_A}/exports")

    assert response.status_code == 200, response.text
    assert response.json()["success"] is True


def test_http_org_admin_of_org_a_cannot_delete_org_b_export(monkeypatch):
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.delete(f"/api/organizations/{ORG_B}/exports/exp-1")

    assert response.status_code == 403, response.text
    assert world.handler_tables == []


def test_http_org_admin_of_org_a_can_delete_own_org_export(monkeypatch):
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.delete(f"/api/organizations/{ORG_A}/exports/exp-1")

    assert response.status_code == 200, response.text
    assert "export_history" in world.queried_tables


def test_http_non_admin_member_cannot_delete_an_export(monkeypatch):
    """Member-level membership must not inherit the admin-only delete."""
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _exports_app(monkeypatch, user, world)

    with TestClient(app) as client:
        response = client.delete(f"/api/organizations/{ORG_A}/exports/exp-1")

    assert response.status_code == 403, response.text


def test_http_unauthenticated_request_is_401(monkeypatch):
    """No membership check may be bypassed by simply omitting credentials."""
    from routes.organizations import exports as exports_module

    world = FakeWorld()
    _install_store(monkeypatch, world)
    monkeypatch.setattr(exports_module, "get_supabase_client", lambda: world)
    app = FastAPI()
    app.include_router(exports_module.router)

    async def _unauthenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[auth.get_current_user] = _unauthenticated

    with TestClient(app) as client:
        response = client.get(f"/api/organizations/{ORG_A}/exports")

    assert response.status_code == 401, response.text

    import inspect

    for factory in (require_org_member, require_org_admin):
        params = inspect.signature(factory()).parameters
        assert "request" in params, f"{factory.__name__}: guard lost Request injection"
        assert params["request"].annotation is auth.Request


# ---------------------------------------------------------------------------
# Static hygiene — the no-parentheses bypass class and the guarded surface
# ---------------------------------------------------------------------------
BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]

#: Guards in ``auth.py`` that are FACTORIES: they must be called, i.e. used as
#: ``Depends(require_x())``. ``Depends(require_x)`` would pass the factory
#: itself, skip the check and inject the checker function instead (verified
#: against FastAPI 0.141.1: HTTP 200 on a route whose guard never ran).
FACTORY_GUARDS = (
    "require_auth",
    "require_admin",
    "require_staff",
    "require_org_member",
    "require_org_admin",
)

ORG_PATH_PARAMS = {"organization_id", "org_id", "organisation_id"}
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
SCOPE_GUARDS = {"require_org_member", "require_org_admin"}


def test_no_factory_guard_is_used_without_parentheses():
    """AST scan of the whole backend for the silent-bypass dependency shape.

    Only ``auth.py`` factory guards are checked: ``api.operations_auth`` and
    ``api.insight_authz`` expose *dependency functions* with the same or similar
    names, and those are correctly used bare.
    """
    offenders = []
    for path in sorted(BACKEND_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - defensive
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "Depends"):
                continue
            if not node.args:
                continue
            inner = node.args[0]
            if isinstance(inner, ast.Name) and inner.id in FACTORY_GUARDS:
                offenders.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} {inner.id}")

    assert offenders == [], (
        "guard factory used without parentheses (the check never runs): "
        + ", ".join(offenders)
    )


def _org_scoped_guarded_routes() -> set:
    """``{ "METHOD /path" }`` for routes that name an org AND use an org guard."""
    found = set()
    for path in sorted(BACKEND_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - defensive
            continue
        prefixes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                prefixes[target.id] = str(kw.value.value)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr in ROUTE_METHODS
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Constant)
                ):
                    continue
                router = decorator.func.value
                router_name = router.id if isinstance(router, ast.Name) else ""
                full = prefixes.get(router_name, "") + str(decorator.args[0].value)
                if not any(
                    f"{{{name}}}" in full for name in ORG_PATH_PARAMS
                ):
                    continue
                guards = set()
                # Depends(...) appears in the signature defaults and decorators.
                for sub in ast.walk(node):
                    if not isinstance(sub, ast.Call):
                        continue
                    func = sub.func
                    func_name = (
                        func.attr
                        if isinstance(func, ast.Attribute)
                        else func.id
                        if isinstance(func, ast.Name)
                        else ""
                    )
                    if func_name != "Depends" or not sub.args:
                        continue
                    inner = sub.args[0]
                    if isinstance(inner, ast.Call):
                        inner = inner.func
                    name = None
                    if isinstance(inner, ast.Name):
                        name = inner.id
                    elif isinstance(inner, ast.Attribute):
                        name = inner.attr
                    if name in SCOPE_GUARDS:
                        guards.add(name)
                if guards:
                    found.add(f"{decorator.func.attr.upper()} {full.strip()}")
    return found


def test_org_scoped_guard_surface_is_frozen():
    """Every organisation-path route guarded by these two guards is enumerated.

    Adding such a route must be a deliberate act: update
    ``FROZEN_ORG_SCOPED_GUARDED_ROUTES`` after confirming the new route really
    enforces exact-tenant authorization (F-05-R1). Losing a route from the set
    means a guard was removed — a release blocker.
    """
    live = _org_scoped_guarded_routes()
    added = sorted(live - FROZEN_ORG_SCOPED_GUARDED_ROUTES)
    removed = sorted(FROZEN_ORG_SCOPED_GUARDED_ROUTES - live)

    assert added == [] and removed == [], (
        f"org-scoped guarded route surface changed. added={added} removed={removed}"
    )


#: Frozen surface of organisation-path routes guarded by ``require_org_member()``
#: or ``require_org_admin()`` at CT-FINAL-01 (87 distinct METHOD+path entries;
#: 102 route declarations share them). Exact-tenant enforcement for all of them
#: is provided centrally by ``auth.enforce_org_path_scope``.
#:
#: CT-MP-SUB-004 — DELIBERATE addition (exactly the act this register exists to
#: require): the customer Manual Processing entitlement read
#: (``GET /api/v3/organizations/{organization_id}/manual-processing``) is
#: organisation-path-scoped and guarded by ``require_org_member()``, so it
#: enforces F-05-R1 exact-tenant authorization and belongs in this set.
FROZEN_ORG_SCOPED_GUARDED_ROUTES: frozenset = frozenset({
    "DELETE /api/organizations/files/{org_id}/files/{file_id}/comments/{comment_id}",
    "DELETE /api/organizations/files/{org_id}/files/{file_id}/permanent",
    "DELETE /api/organizations/team/{org_id}/members/{member_id}",
    "DELETE /api/organizations/{org_id}/assets/{asset_id}",
    "DELETE /api/organizations/{org_id}/exports/{export_id}",
    "DELETE /api/organizations/{org_id}/facilities/{facility_id}",
    "GET /api/customer-documents/documents/{org_id}",
    "GET /api/customer-documents/pending/{org_id}",
    "GET /api/customer-documents/stats/{org_id}",
    "GET /api/documents/organizations/{org_id}/documents/activity",
    "GET /api/documents/stats/{org_id}",
    "GET /api/documents/{org_id}",
    "GET /api/documents/{org_id}/{file_id}/status",
    "GET /api/organizations/data/organizations/{org_id}/assets",
    "GET /api/organizations/data/{org_id}/defra-factors",
    "GET /api/organizations/data/{org_id}/emissions-data",
    "GET /api/organizations/data/{org_id}/emissions/export-csv",
    "GET /api/organizations/files/organizations/{org_id}/files/stats",
    "GET /api/organizations/files/{org_id}/files/archived",
    "GET /api/organizations/files/{org_id}/files/{file_id}/comments",
    "GET /api/organizations/files/{org_id}/files/{file_id}/versions",
    "GET /api/organizations/files/{org_id}/files/{file_id}/versions/{version_id}",
    "GET /api/organizations/members/{org_id}/members/roles",
    "GET /api/organizations/members/{org_id}/members/stats",
    "GET /api/organizations/team/{org_id}/members",
    "GET /api/organizations/{org_id}/assets",
    "GET /api/organizations/{org_id}/assets/stats",
    "GET /api/organizations/{org_id}/dashboard-summary",
    "GET /api/organizations/{org_id}/exports",
    "GET /api/organizations/{org_id}/exports/{export_id}/download",
    "GET /api/organizations/{org_id}/facilities",
    "GET /api/organizations/{org_id}/facilities/stats",
    "GET /api/organizations/{org_id}/metadata/all",
    "GET /api/organizations/{org_id}/metadata/contacts",
    "GET /api/organizations/{org_id}/metadata/custom-metrics",
    "GET /api/organizations/{org_id}/metadata/employees",
    "GET /api/organizations/{org_id}/metadata/financials",
    "GET /api/organizations/{org_id}/metadata/industry",
    "GET /api/organizations/{org_id}/metadata/required-fields",
    "GET /api/organizations/{org_id}/metadata/sustainability",
    "GET /api/organizations/{org_id}/organization-activity",
    "GET /api/v3/organizations/{org_id}",
    "GET /api/v3/organizations/{org_id}/assets",
    "GET /api/v3/organizations/{org_id}/consultant-engagements",
    "GET /api/v3/organizations/{org_id}/facilities",
    "GET /api/v3/organizations/{org_id}/invitations",
    "GET /api/v3/organizations/{org_id}/members",
    "GET /api/v3/organizations/{org_id}/metadata",
    "GET /api/v3/organizations/{org_id}/profile",
    "GET /api/v3/organizations/{org_id}/roles",
    "GET /api/v3/organizations/{organization_id}/applicability",
    # CT-MP-SUB-004 — customer Manual Processing entitlement (require_org_member,
    # F-05-R1 exact-tenant enforced).
    "GET /api/v3/organizations/{organization_id}/manual-processing",
    "GET /api/{org_id}/emissions",
    "PATCH /api/organizations/team/{org_id}/members/{member_id}",
    "PATCH /api/organizations/{org_id}/facilities/{facility_id}",
    "POST /api/documents/{org_id}/{file_id}/review",
    "POST /api/organizations/files/api/organizations/{org_id}/files/upload",
    "POST /api/organizations/files/{org_id}/files/{file_id}/archive",
    "POST /api/organizations/files/{org_id}/files/{file_id}/comments",
    "POST /api/organizations/files/{org_id}/files/{file_id}/restore",
    "POST /api/organizations/files/{org_id}/files/{file_id}/versions",
    "POST /api/organizations/members/{org_id}/members/bulk/remove",
    "POST /api/organizations/members/{org_id}/members/bulk/update",
    "POST /api/organizations/team/{org_id}/invite",
    "POST /api/organizations/{org_id}/assets",
    "POST /api/organizations/{org_id}/assets/bulk/create",
    "POST /api/organizations/{org_id}/exports/exports/emissions",
    "POST /api/organizations/{org_id}/facilities",
    "POST /api/organizations/{org_id}/members/bulk/invite",
    "POST /api/organizations/{org_id}/metadata/validate",
    "POST /api/v3/organizations/{org_id}/assets",
    "POST /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/accept",
    "POST /api/v3/organizations/{org_id}/consultant-engagements/{engagement_id}/reject",
    "POST /api/v3/organizations/{org_id}/facilities",
    "POST /api/v3/organizations/{org_id}/invitations",
    "POST /api/v3/organizations/{org_id}/members",
    "POST /api/v3/organizations/{organization_id}/applicability",
    "PUT /api/organizations/files/{org_id}/files/{file_id}/comments/{comment_id}",
    "PUT /api/organizations/{org_id}/assets/{asset_id}",
    "PUT /api/organizations/{org_id}/facilities/{facility_id}",
    "PUT /api/organizations/{org_id}/metadata/contacts",
    "PUT /api/organizations/{org_id}/metadata/custom-metrics",
    "PUT /api/organizations/{org_id}/metadata/employees",
    "PUT /api/organizations/{org_id}/metadata/financials",
    "PUT /api/organizations/{org_id}/metadata/industry",
    "PUT /api/organizations/{org_id}/metadata/sustainability",
    "PUT /api/v3/organizations/{org_id}/metadata",
    "PUT /api/v3/organizations/{org_id}/profile",
})


# ---------------------------------------------------------------------------
# Admin authority is exact-tenant too (F-05-R1 for ``require_org_admin()``)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_of_org_a_is_denied_on_org_b_path(monkeypatch):
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    _install_store(monkeypatch, world)
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403
    assert "admin privileges required" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_admin_of_org_a_is_allowed_on_org_a_path_without_db_call(monkeypatch):
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    _install_store(monkeypatch, world)
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")

    assert await _admin_guard(user, {"org_id": ORG_A}) is user
    assert world.queries == []


@pytest.mark.asyncio
async def test_owner_of_org_a_is_allowed_on_org_a_path(monkeypatch):
    world = FakeWorld([_membership("u-owner", ORG_A, "owner")])
    _install_store(monkeypatch, world)
    user = org_owner_user(ORG_A, "u-owner", "o@carbontally.test")

    assert await _admin_guard(user, {"org_id": ORG_A}) is user


@pytest.mark.asyncio
async def test_stale_token_role_falls_back_to_the_membership_row(monkeypatch):
    """A token that says ``user`` but whose membership row says ``admin``.

    This is the authoritative fallback F-05-R3 rewrote (list query, not
    ``maybe_single``).
    """
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    _install_store(monkeypatch, world)
    user = member_user(ORG_A, "u-admin", "a@carbontally.test")

    assert await _admin_guard(user, {"org_id": ORG_A}) is user
    assert world.queries[0][0] == "organization_members"
    assert world.single_used is False


@pytest.mark.asyncio
async def test_multi_org_owner_is_allowed_on_each_org_they_own(monkeypatch):
    world = FakeWorld(
        [
            _membership("u-owner", ORG_A, "owner"),
            _membership("u-owner", ORG_B, "owner"),
        ]
    )
    _install_store(monkeypatch, world)
    user = org_owner_user(ORG_A, "u-owner", "o@carbontally.test")

    assert await _admin_guard(user, {"org_id": ORG_A}) is user
    assert await _admin_guard(user, {"org_id": ORG_B}) is user


@pytest.mark.asyncio
async def test_admin_of_org_a_is_not_admin_of_org_b_where_they_are_a_member(monkeypatch):
    world = FakeWorld(
        [
            _membership("u-admin", ORG_A, "admin"),
            _membership("u-admin", ORG_B, "member"),
        ]
    )
    _install_store(monkeypatch, world)
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_internal_system_admin_keeps_global_admin_authority(monkeypatch):
    """CarbonTally internal admin is cross-organisation by design (approved)."""
    _install_store(monkeypatch, FakeWorld())
    user = staff_user("u-sysadmin", role_name="admin")

    assert user.is_internal_staff is True
    assert await _admin_guard(user, {"org_id": ORG_B}) is user


@pytest.mark.asyncio
async def test_entity_staff_named_admin_gets_no_global_admin_authority(monkeypatch):
    """D20 scope-first: a Processing Entity profile is never a global admin."""
    _install_store(monkeypatch, FakeWorld())
    user = entity_operator_user("entity-1")
    user.role = "admin"
    user.role_name = "admin"
    user.permissions = {"is_superuser": True}

    with pytest.raises(HTTPException) as exc:
        await _admin_guard(user, {"org_id": ORG_B})

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_guard_without_path_org_keeps_historical_behaviour(monkeypatch):
    """Routes with no organisation in the path are unchanged by F-05-R1."""
    world = FakeWorld([_membership("u-admin", ORG_A, "admin")])
    _install_store(monkeypatch, world)
    user = org_admin_user(ORG_A, "u-admin", "a@carbontally.test")

    assert await _admin_guard(user, {}) is user
    assert await _admin_guard(user, None) is user


# ---------------------------------------------------------------------------
# The COMPOSED legacy application (backend/main.py) — the surface that serves
# the reported route. Verifies the fix is reachable where it matters, not only
# on a standalone router app.
# ---------------------------------------------------------------------------
def test_composed_legacy_app_exposes_and_guards_the_reported_route(monkeypatch):
    import warnings

    import main as legacy_main

    target = "/api/organizations/{org_id}/exports/exports/emissions"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        schema = legacy_main.app.openapi()
    assert target in schema["paths"], "the composed app must serve the reported route"
    assert "post" in schema["paths"][target]

    # The app's OpenAPI build caches the flattened router; the dependency
    # override below therefore applies to the real request path.
    world = FakeWorld([_membership("u-member", ORG_A, "member")])
    _install_store(monkeypatch, world)

    from routes.organizations import exports as exports_module

    monkeypatch.setattr(exports_module, "get_supabase_client", lambda: world)

    user = member_user(ORG_A, "u-member", "m@carbontally.test")

    async def _override():
        return user

    legacy_main.app.dependency_overrides[auth.get_current_user] = _override
    try:
        with TestClient(legacy_main.app) as client:
            cross = client.post(
                f"/api/organizations/{ORG_B}/exports/exports/emissions",
                json={"format": "csv"},
            )
            assert cross.status_code == 403, cross.text
            # Checked before the same-tenant request, which does read the table.
            assert world.handler_tables == []

            own = client.post(
                f"/api/organizations/{ORG_A}/exports/exports/emissions",
                json={"format": "csv"},
            )
    finally:
        legacy_main.app.dependency_overrides.pop(auth.get_current_user, None)

    assert own.status_code == 200, own.text


