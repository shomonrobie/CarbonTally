"""V3 vehicles surface (D17) — route registration + authorization posture.

Unit-level: the vehicles routes are registered and carry the same
authorization posture as facilities/assets (org member reads; org admin
writes). RLS for the table is verified by the migration and integration
suites.
"""
from __future__ import annotations

from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/vehicles",
    "/api/v3/vehicles/{vehicle_id}",
)


def test_v3_vehicles_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 vehicles routes: {missing}"


def _route_dependencies(router, path_fragment: str) -> list:
    found: list = []
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        original = getattr(route, "original_router", None)
        if path and path_fragment in path:
            dependant = getattr(route, "dependant", None)
            if dependant is not None:
                methods = sorted(getattr(route, "methods", []) or [])
                for dep in dependant.dependencies:
                    found.append((methods, dep.call))
        if original is not None:
            found.extend(_route_dependencies(original, path_fragment))
    return found


def _guard_names(router, fragment: str, method: str | None = None) -> set[str]:
    names: set[str] = set()
    for methods, call in _route_dependencies(router, fragment):
        if method is not None and method not in methods:
            continue
        names.add(getattr(call, "__name__", ""))
    return names


def test_vehicles_reads_are_org_member_gated() -> None:
    from api.v3_vehicles import router as vehicles_router

    # GET list + GET by id are member reads.
    assert "org_member_checker" in _guard_names(vehicles_router, "/api/v3/vehicles", "GET")


def test_vehicles_writes_are_org_admin_gated() -> None:
    from api.v3_vehicles import router as vehicles_router

    for method in ("POST", "PUT", "DELETE"):
        names = _guard_names(vehicles_router, "/api/v3/vehicles", method)
        assert "org_admin_checker" in names, f"{method} /api/v3/vehicles must be org-admin gated, got {names}"
