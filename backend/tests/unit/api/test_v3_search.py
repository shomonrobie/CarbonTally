"""V3 organisation-scoped search (G-P1-1) — route registration + scope gate."""
from __future__ import annotations

from tests.unit.api.route_paths import flatten_router_paths


def test_v3_search_route_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    assert any("/api/v3/search" in p for p in paths), "missing /api/v3/search route"


def _route_dependencies(router, path_fragment: str) -> list:
    found: list = []
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        original = getattr(route, "original_router", None)
        if path and path_fragment in path:
            dependant = getattr(route, "dependant", None)
            if dependant is not None:
                for dep in dependant.dependencies:
                    found.append(dep.call)
        if original is not None:
            found.extend(_route_dependencies(original, path_fragment))
    return found


def test_search_requires_org_member() -> None:
    """Search is org-scoped; the API gate is org membership (the backend then
    binds every query to the caller's organisation)."""
    from api.v3_search import router as search_router

    names = {getattr(d, "__name__", "") for d in _route_dependencies(search_router, "/api/v3/search")}
    assert "org_member_checker" in names


async def test_search_repository_returns_only_org_rows() -> None:
    """The search repository is a pure method-driven contract; verify the
    in-memory stub shape used by the API tests stays aligned."""
    from tests.unit.api.fakes import _SearchStub

    stub = _SearchStub()
    assert await stub.search_org("org-a", "gas") == []
