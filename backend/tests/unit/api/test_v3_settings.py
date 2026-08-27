"""V3 platform settings surface (N3 — configurable retention).

Route registration + authorization posture + no-invented-durations behaviour.
"""
from __future__ import annotations

from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/settings/retention",
)


def test_v3_settings_retention_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 settings routes: {missing}"


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


def test_retention_settings_require_internal_staff_admin() -> None:
    from api.v3_settings import router as settings_router

    names: set[str] = set()
    for methods, call in _route_dependencies(settings_router, "/api/v3/settings/retention"):
        names.add(getattr(call, "__name__", ""))
    # require_admin() -> admin_checker; the general-staff door stays shut.
    assert "admin_checker" in names


async def test_retention_get_returns_none_for_unset_values() -> None:
    """Unset retention durations surface as None — never an invented policy."""
    from api.v3_settings import get_retention_settings
    from auth import AuthUser
    from tests.unit.api.fakes import _SettingsStub

    class _Repos:
        settings = _SettingsStub()

    user = AuthUser(user_id="u-admin", email="a@ct.test", role="admin", role_name="admin", is_staff=True)
    result = await get_retention_settings(user, _Repos())
    settings = result["settings"]
    assert settings["audit_log_retention_days"] is None
    assert settings["data_retention_days"] is None
    assert settings["document_retention_days"] is None
    assert settings["backup_retention_days"] is None
