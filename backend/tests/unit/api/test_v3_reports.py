"""V3 reports surface (Phase 5) — route registration + helpers + API behaviour.

The authoritative report-generation logic lives in ``engines/report_generation.py``
(tested by the engine suites); these tests cover the V3 reporting surface
wiring: route registration, the pure shaping/validation helpers, and the
API behaviours (listing, generation lifecycle, retrieval, preview, versions,
download, org isolation and authorization) against the in-memory world.
"""
from __future__ import annotations

import asyncio

import pytest

from api.dependencies import get_report_engine
from api.v3_reports import (
    REPORT_STATUSES,
    SUPPORTED_REPORT_TYPES,
    default_report_name,
    shape_report_out,
    shape_report_status,
    validate_report_status,
    validate_report_type,
)
from tests.unit.api.fakes import member_user
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/reports",
    "/api/v3/reports/{report_id}",
    "/api/v3/reports/{report_id}/content",
    "/api/v3/reports/{report_id}/versions",
    "/api/v3/reports/{report_id}/download",
    "/api/v3/reports/types",
)


def test_v3_reports_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 reports routes: {missing}"


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_supported_report_types_are_real_engine_types() -> None:
    # Only the types the V3 engine genuinely produces are offered.
    assert "annual" in SUPPORTED_REPORT_TYPES
    assert "summary" not in SUPPORTED_REPORT_TYPES  # legacy-only label


def test_validate_report_type_accepts_supported() -> None:
    validate_report_type("annual")  # must not raise


def test_validate_report_type_rejects_unsupported() -> None:
    with pytest.raises(Exception) as exc_info:
        validate_report_type("summary")
    assert exc_info.value.status_code == 422  # type: ignore[attr-defined]


def test_validate_report_status_rejects_unknown() -> None:
    with pytest.raises(Exception) as exc_info:
        validate_report_status("published")
    assert exc_info.value.status_code == 422  # type: ignore[attr-defined]


def test_validate_report_status_accepts_persisted_statuses() -> None:
    for status in REPORT_STATUSES:
        validate_report_status(status)  # must not raise


def test_default_report_name_derives_from_real_metadata() -> None:
    assert default_report_name("annual", 2025) == "Annual emissions report 2025"


def test_shape_report_status_ready_only_when_completed_with_content() -> None:
    # Completed with content + artefact details → ready.
    ready = shape_report_status(
        {
            "status": "completed",
            "generated_content": {"content": {"totals": {}}},
            "final_report_url": "storage/reports/r1.json",
            "page_count": 12,
        }
    )
    assert ready["status_label"] == "Ready"
    assert ready["ready"] is True

    # Pending → not ready.
    pending = shape_report_status(
        {
            "status": "pending",
            "generated_content": None,
            "final_report_url": "",
            "page_count": 0,
        }
    )
    assert pending["status_label"] == "Queued"
    assert pending["ready"] is False

    # Completed but with no persisted content → NOT ready (never invented).
    empty = shape_report_status(
        {
            "status": "completed",
            "generated_content": None,
            "final_report_url": "",
            "page_count": 0,
        }
    )
    assert empty["ready"] is False


def test_shape_report_out_adds_version_and_period() -> None:
    shaped = shape_report_out(
        {"reporting_year": 2025, "status": "completed"},
        {"version_number": 1, "is_current": True},
    )
    assert shaped["current_version"]["version_number"] == 1
    assert shaped["reporting_period"]["start_date"] == "2025-01-01"
    assert shaped["reporting_period"]["end_date"] == "2025-12-31"


# ---------------------------------------------------------------------------
# API behaviours (in-memory world)
# ---------------------------------------------------------------------------


def _seed_completed_report(
    world, report_id: str = "rep-1", org_id: str = "org-a", year: int = 2025
) -> dict:
    return world.reports.seed_report(
        report_id=report_id,
        org_id=org_id,
        year=year,
        status="completed",
        content={
            "page_count": 12,
            "content": {
                "metadata": {"report_type": "annual"},
                "totals": {"total_co2e_kg": "183.000000"},
            },
        },
    )


def test_list_reports_org_isolated(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-a", org_id="org-a")
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))

    response = client.get("/api/v3/reports", params={"organization_id": "org-a"})
    assert response.status_code == 200
    body = response.json()
    assert [r["id"] for r in body["reports"]] == ["rep-a"]
    assert body["count_by_status"]["completed"] == 1


def test_list_reports_org_isolation_denied(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))

    response = client.get("/api/v3/reports", params={"organization_id": "org-b"})
    assert response.status_code == 403


def test_list_reports_requires_org_member(client, world, user_provider) -> None:
    _seed_completed_report(world)
    response = client.get("/api/v3/reports", params={"organization_id": "org-a"})
    # Default fixture user is staff, not an org member → 403.
    assert response.status_code == 403


def test_list_reports_rejects_unknown_status_filter(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get(
        "/api/v3/reports",
        params={"organization_id": "org-a", "status": "published"},
    )
    assert response.status_code == 422


def test_list_reports_filters_by_type_year_status(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-2024", org_id="org-a", year=2024)
    world.reports.seed_report(
        report_id="rep-2025",
        org_id="org-a",
        status="failed",
        error_log="validation failed",
    )
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))

    failed = client.get(
        "/api/v3/reports",
        params={"organization_id": "org-a", "status": "failed"},
    ).json()
    assert [r["id"] for r in failed["reports"]] == ["rep-2025"]

    year = client.get(
        "/api/v3/reports",
        params={"organization_id": "org-a", "reporting_year": 2024},
    ).json()
    assert [r["id"] for r in year["reports"]] == ["rep-2024"]


def test_report_types_endpoint(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/types")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()["report_types"]]
    assert ids == ["annual"]


def test_generate_report_success_lifecycle(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-a", "report_type": "annual", "reporting_year": 2025},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    report = body["report"]
    assert report["status"] == "completed"
    assert report["status_label"] == "Ready"
    assert report["ready"] is True
    assert report["report_name"] == "Annual emissions report 2025"
    assert report["created_by"] == "user-a"
    # Content comes from the authoritative engine (no fabricated totals).
    assert body["content"]["totals"]["total_co2e_kg"] == "183.000000"
    # A version snapshot was recorded on the existing report_versions surface.
    assert report["current_version"]["version_number"] == 1


def test_generate_report_records_version_history(client, world, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-a", "report_type": "annual", "reporting_year": 2025},
    )
    report_id = response.json()["report"]["id"]
    versions = client.get(f"/api/v3/reports/{report_id}/versions")
    assert versions.status_code == 200
    rows = versions.json()["versions"]
    assert len(rows) == 1
    assert rows[0]["version_number"] == 1
    assert rows[0]["is_current"] is True


def test_generate_report_org_isolation(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-b", "report_type": "annual", "reporting_year": 2025},
    )
    assert response.status_code == 403


def test_generate_report_invalid_reporting_year(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-a", "report_type": "annual", "reporting_year": 1800},
    )
    assert response.status_code == 422


def test_generate_report_unsupported_type(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-a", "report_type": "summary", "reporting_year": 2025},
    )
    assert response.status_code == 422


def test_generate_report_failure_marks_row_failed(client, app, world, user_provider) -> None:
    class _FailingEngine:
        async def generate(self, request, report_id=None):
            from core.exceptions import ReportGenerationFailedError

            raise ReportGenerationFailedError("boom")

    async def _fail_engine_dependency():
        return _FailingEngine()

    app.dependency_overrides[get_report_engine] = _fail_engine_dependency
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.post(
        "/api/v3/reports",
        json={"organization_id": "org-a", "report_type": "annual", "reporting_year": 2025},
    )
    assert response.status_code == 500
    # The queue row is marked failed with the real error — never left pending.
    rows = world.reports._rows
    failed = [r for r in rows.values() if r["organization_id"] == "org-a"]
    assert failed and failed[0]["status"] == "failed"
    assert "boom" in failed[0]["error_log"]


def test_get_report_returns_detail(client, world, user_provider) -> None:
    _seed_completed_report(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/rep-1")
    assert response.status_code == 200
    report = response.json()["report"]
    assert report["id"] == "rep-1"
    assert report["status"] == "completed"
    assert report["ready"] is True


def test_get_report_nonexistent_returns_404(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/does-not-exist")
    assert response.status_code == 404


def test_get_report_org_isolation(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/reports/rep-b").status_code == 403


def test_get_report_content_preview(client, world, user_provider) -> None:
    _seed_completed_report(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/rep-1/content")
    assert response.status_code == 200
    assert response.json()["content"]["totals"]["total_co2e_kg"] == "183.000000"


def test_get_report_content_not_ready(client, world, user_provider) -> None:
    world.reports.seed_report(report_id="rep-pending", org_id="org-a", status="pending")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/rep-pending/content")
    assert response.status_code == 409


def test_get_report_content_org_isolation(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/reports/rep-b/content").status_code == 403


def test_download_report_returns_content_attachment(client, world, user_provider) -> None:
    _seed_completed_report(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/rep-1/download")
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    payload = response.json()
    assert payload["report_id"] == "rep-1"
    assert payload["status"] == "completed"


def test_download_report_org_isolation(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/reports/rep-b/download").status_code == 403


def test_download_report_not_ready(client, world, user_provider) -> None:
    world.reports.seed_report(report_id="rep-pending", org_id="org-a", status="pending")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/reports/rep-pending/download").status_code == 409


def test_versions_org_isolation(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-b", org_id="org-b")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/reports/rep-b/versions").status_code == 403


def test_versions_empty_for_new_report(client, world, user_provider) -> None:
    _seed_completed_report(world, report_id="rep-1", org_id="org-a")
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/rep-1/versions")
    assert response.status_code == 200
    assert response.json()["versions"] == []


def test_report_version_roundtrip(client, world, user_provider) -> None:
    _seed_completed_report(world)
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    asyncio.run(
        world.report_versions.create(
            "rep-1",
            version_number=1,
            content={"totals": {"total_co2e_kg": "183.000000"}},
            created_by="user-a",
            is_current=True,
        )
    )
    response = client.get("/api/v3/reports/rep-1")
    assert response.json()["report"]["current_version"]["version_number"] == 1


# ---------------------------------------------------------------------------
# Export authorization (existing /api/v3/exports surface, org-isolated)
# ---------------------------------------------------------------------------


def test_exports_csv_org_isolated(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/exports/emissions.csv", params={"organization_id": "org-a"})
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")


def test_exports_csv_org_isolation_denied(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/exports/emissions.csv", params={"organization_id": "org-b"})
    assert response.status_code == 403


def test_exports_json_org_isolation_denied(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/exports/emissions.json", params={"organization_id": "org-b"})
    assert response.status_code == 403


def test_exports_documents_org_isolation_denied(client, user_provider) -> None:
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/exports/documents.csv", params={"organization_id": "org-b"})
    assert response.status_code == 403


def test_exports_requires_org_member(client, user_provider) -> None:
    # Default fixture user is staff (not an org member) → 403.
    response = client.get("/api/v3/exports/emissions.csv", params={"organization_id": "org-a"})
    assert response.status_code == 403





# ---------------------------------------------------------------------------
# D27 / D19 §18 — white-label PDF download
# ---------------------------------------------------------------------------


def test_report_pdf_download_branded(world, client, user_provider) -> None:
    """A completed report renders a branded PDF via the server-authorized brand."""
    world.reports.seed_report(
        report_id="report-pdf-1", org_id="org-a", status="completed",
        content={"content": {"totals": {"total_co2e_kg": "10.5"}, "organization": {"name": "Org A"}}},
    )
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/report-pdf-1/pdf")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_report_pdf_not_ready(world, client, user_provider) -> None:
    """A non-completed report must not render a PDF."""
    world.reports.seed_report(
        report_id="report-pdf-pending", org_id="org-a", status="pending"
    )
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/report-pdf-pending/pdf")
    assert response.status_code == 409


def test_report_pdf_foreign_org_denied(world, client, user_provider) -> None:
    """A report PDF is org-isolated like every other report artefact."""
    world.reports.seed_report(
        report_id="report-pdf-2", org_id="org-b", status="completed",
        content={"content": {"totals": {"total_co2e_kg": "1"}}},
    )
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    response = client.get("/api/v3/reports/report-pdf-2/pdf")
    assert response.status_code == 403
