"""Phase: legacy capability reimplementation — verify the new V3 routes are
registered on the V3 router (organizations, members, facilities, assets,
upload, documents, batches, review, SLA, verifications, notifications, exports).
"""
from __future__ import annotations

from api.router import router as v3_router
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/organizations/",
    "/api/v3/organizations/{org_id}/members",
    "/api/v3/organizations/{org_id}/facilities",
    "/api/v3/organizations/{org_id}/assets",
    "/api/v3/uploads",
    "/api/v3/documents",
    "/api/v3/batches",
    "/api/v3/admin/review-queue",
    "/api/v3/admin/sla/settings",
    "/api/v3/verifications",
    "/api/v3/notifications",
    "/api/v3/exports",
)


def test_v3_legacy_reimplementation_routes_registered() -> None:
    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 reimplementation routes: {missing}"
