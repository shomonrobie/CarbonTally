"""V3 new capabilities — verify the new routes are registered on the V3 router
(consultants, multi-client grants, processing companies, manual extraction, QC,
suppliers).
"""
from __future__ import annotations

from api.router import router as v3_router
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/consultants/me",
    "/api/v3/consultants/me/clients",
    "/api/v3/consultants/me/team",
    "/api/v3/consultants/me/tasks",
    "/api/v3/processing-entities",
    "/api/v3/manual-extraction/batches",
    "/api/v3/manual-extraction/items",
    "/api/v3/qc/queue",
    "/api/v3/qc/items",
    "/api/v3/suppliers",
)


def test_v3_new_capabilities_routes_registered() -> None:
    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 new-capability routes: {missing}"
