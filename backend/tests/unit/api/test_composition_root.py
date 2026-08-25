"""Phase 1 — verify the single FastAPI composition root serves BOTH surfaces.

`backend/main.py` is the canonical application: it mounts the legacy route tree
(transition surface) and the V3 (v2.1) API on one app, exposing one OpenAPI.
"""
from __future__ import annotations

import main  # noqa: E402  (imports the full composition root)

from tests.unit.api.route_paths import flatten_router_paths

LEGACY_PATH_FRAGMENTS = (
    "/health",
    "/api/users",
    "/api/upload",
    "/api/documents",
    "/api/admin/staff",
    "/api/admin/reviews",
    "/api/organizations/",
)

V3_PATH_FRAGMENTS = (
    "/api/v2/factor-match",
    "/api/v2/calculate",
    "/api/v2/validate",
    "/api/v2/generate-report",
    "/api/v3/customer-factors",
    "/api/v3/issues",
    "/api/v3/admin/entities",
)


def _route_paths() -> set:
    return flatten_router_paths(main.app)


def test_composition_root_serves_legacy_surface() -> None:
    paths = _route_paths()
    missing = [
        fragment for fragment in LEGACY_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"legacy routes missing: {missing}"


def test_composition_root_serves_v3_surface() -> None:
    paths = _route_paths()
    missing = [
        fragment for fragment in V3_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"V3 routes missing: {missing}"
