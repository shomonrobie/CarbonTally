"""Phase 1 — verify the V3 (v2.1) engine endpoints are exposed on the V3 router.

These are the Phase-1 mandated capabilities: factor-match, calculate, validate,
customer-factors, issues, reports (generate-report), processing entities — plus
the supporting v2.1 admin surfaces that ship with them.
"""
from __future__ import annotations

from api.router import router as v3_router
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v2/factor-match",
    "/api/v2/calculate",
    "/api/v2/validate",
    "/api/v2/generate-report",
    "/api/v2/benchmark",
    "/api/v3/customer-factors",
    "/api/v3/issues",
    "/api/v3/admin/entities",
    "/api/v2/admin/aliases",
    "/api/v2/admin/imports",
    "/api/v2/admin/providers",
    "/api/v2/admin/audit",
    "/api/v3/reports",
    "/api/v3/reports/{report_id}",
    "/api/v3/reports/types",
    "/api/v3/reports/{report_id}/download",
    "/api/v3/exports",
)


def test_v3_router_exposes_phase1_endpoints() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 endpoints: {missing}"
    assert len(paths) > 0, "V3 router must carry at least one route"
