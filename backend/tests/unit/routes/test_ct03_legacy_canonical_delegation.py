"""CT-IMPLEMENT-03 — route-layer reconciliation and retired-table regression.

Two things are asserted here that no amount of unit testing of the services can
establish:

1. **The retired tables are gone from the runtime.** Every Python module under
   ``backend/`` except the tests themselves is scanned for an *access* to the
   retired legacy schedule/share tables. A module or handler whose name merely
   contains the words is not an access; a Supabase ``from_(...)`` or a SQL
   ``FROM``/``INTO``/``UPDATE``/``DELETE FROM`` that names the table is.
2. **The legacy surfaces delegate to the canonical implementation** — the same
   service the canonical ``/api/v3`` routes use — and advertise the canonical
   frequency vocabulary, so F-1 and F-2 cannot silently return.
"""
from __future__ import annotations

import pathlib
import re
import uuid
from datetime import datetime, time, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.responses import Response

import routes.reports as legacy
from auth import AuthUser
from tests.unit.api.route_paths import flatten_router_paths

BACKEND = pathlib.Path("/home/shomonrobie/ct_93d5cdd/backend")

#: SQL/PostgREST access to a retired table. Deliberately about *access*.
_RETIRED_TABLE_ACCESS = (
    re.compile(r"from_\(\s*['\"]report_schedules['\"]"),
    re.compile(r"from_\(\s*['\"]report_history['\"]"),
    re.compile(r"\bFROM\s+public\.report_schedules\b", re.IGNORECASE),
    re.compile(r"\bFROM\s+public\.report_history\b", re.IGNORECASE),
    re.compile(r"\bINTO\s+public\.report_schedules\b", re.IGNORECASE),
    re.compile(r"\bUPDATE\s+public\.report_history\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\s+public\.report_history\b", re.IGNORECASE),
)

#: Modules whose docstrings *document* what was retired; they are still scanned,
#: because documenting a retired table is not accessing one — the patterns above
#: match access only.


def runtime_modules() -> list[pathlib.Path]:
    """Every non-test Python module shipped under ``backend/``."""
    return [
        path
        for path in BACKEND.rglob("*.py")
        if ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and "tests" not in path.parts
    ]


def test_no_runtime_module_accesses_a_retired_report_table():
    offenders = []
    for path in runtime_modules():
        text = path.read_text(errors="ignore")
        for pattern in _RETIRED_TABLE_ACCESS:
            if pattern.search(text):
                offenders.append(f"{path.relative_to(BACKEND)}: {pattern.pattern}")
    assert offenders == [], "retired-table access still present: " + "; ".join(offenders)


def test_legacy_reports_module_names_no_retired_table_at_all():
    """The legacy router must not name the retired tables as a data source.

    Its module/handler/action names legitimately contain the words (for example
    ``services.report_schedules``, the canonical module, and the action label
    ``"get_report_schedules"``), so the assertion targets *access*, plus the
    absence of any mention of the retired share table at all.
    """
    text = (BACKEND / "routes/reports.py").read_text()
    assert "report_history" not in text
    for pattern in _RETIRED_TABLE_ACCESS:
        assert not pattern.search(text), pattern.pattern


def test_the_schedule_and_share_services_are_the_shared_implementation():
    """One implementation, two surfaces: the legacy router delegates to it."""
    text = (BACKEND / "routes/reports.py").read_text()
    assert "ReportScheduleService(repos)" in text
    assert "ReportShareService(repos)" in text
    assert "shape_schedule(" in text and "shape_share(" in text


# ---------------------------------------------------------------------------
# Legacy delegation: frequencies, schedule CRUD, sharing
# ---------------------------------------------------------------------------
def org_owner(**overrides) -> AuthUser:
    values = {
        "user_id": "user-1",
        "email": "owner@example.com",
        "role": "org_owner",
        "role_name": "owner",
        "organization_id": "org-1",
    }
    values.update(overrides)
    return AuthUser(**values)


def schedule_row(**overrides) -> dict:
    values = {
        "id": str(uuid.uuid4()),
        "organization_id": "org-1",
        "name": "Annual pack",
        "report_type": "annual",
        "reporting_year": 2025,
        "period_start": None,
        "period_end": None,
        "recipients": [{"user_id": None, "email": "owner@example.com"}],
        "frequency": "monthly",
        "run_time": time(7, 0),
        "timezone": "Europe/London",
        "is_active": True,
        "paused_at": None,
        "created_by": "user-1",
        "created_at": datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
        "updated_at": None,
        "next_run_at": datetime(2026, 4, 10, 6, 0, tzinfo=timezone.utc),
        "last_run_at": None,
        "last_result": None,
        "last_error": None,
        "failure_count": 0,
        "retry_policy": {"max_attempts": 3, "backoff_minutes": [5, 30, 120]},
    }
    values.update(overrides)
    return values


async def test_frequencies_endpoint_advertises_the_canonical_vocabulary():
    response = Response()
    payload = await legacy.get_schedule_frequencies(
        response=response, current_user=org_owner()
    )

    values = [item["value"] for item in payload["frequencies"]]
    assert values == ["weekly", "monthly", "quarterly", "annual"]
    assert "daily" not in values, "the retired advertisement must be gone"
    assert response.headers["Deprecation"] == "true"
    assert "/api/v3/reports" in response.headers["Link"]


class RecordingScheduleService:
    """Stand-in for the canonical service (records the canonical call)."""

    calls: list[dict] = []
    created: dict = {}
    deleted: bool = True

    def __init__(self, repos) -> None:
        self._repos = repos

    async def create(self, organization_id, **kwargs):
        RecordingScheduleService.calls.append({"organization_id": organization_id, **kwargs})
        return RecordingScheduleService.created

    async def delete(self, organization_id, schedule_id, *, actor):
        RecordingScheduleService.calls.append(
            {"delete": schedule_id, "organization_id": organization_id, "actor": actor}
        )
        return RecordingScheduleService.deleted

    async def list_schedules(self, organization_id, **kwargs):
        return {"schedules": [RecordingScheduleService.created], "total": 1, "frequencies": []}


@pytest.fixture
def recording_service(monkeypatch):
    RecordingScheduleService.calls = []
    RecordingScheduleService.created = schedule_row()
    RecordingScheduleService.deleted = True
    monkeypatch.setattr(legacy, "ReportScheduleService", RecordingScheduleService)
    return RecordingScheduleService


async def test_legacy_create_delegates_the_canonical_configuration(recording_service):
    response = Response()
    payload = legacy.LegacyScheduleCreate(
        name="Annual pack",
        report_type="annual",
        reporting_year=2025,
        frequency="monthly",
        run_time="07:00",
        recipients=["owner@example.com"],
    )

    body = await legacy.create_report_schedule(
        schedule_data=payload,
        response=response,
        current_user=org_owner(),
        repos=SimpleNamespace(),
    )

    call = recording_service.calls[0]
    assert call["organization_id"] == "org-1"
    assert call["actor"] == "user-1"
    assert call["frequency"] == "monthly"
    assert call["run_time"] == time(7, 0)
    assert call["timezone_name"] == "Europe/London"
    assert body["schedule"]["id"] == recording_service.created["id"]
    assert response.headers["Deprecation"] == "true"


async def test_legacy_create_defaults_the_organisation_to_the_caller(recording_service):
    await legacy.create_report_schedule(
        schedule_data=legacy.LegacyScheduleCreate(
            name="A", reporting_year=2025, frequency="annual", recipients=["a@b.com"]
        ),
        response=Response(),
        current_user=org_owner(),
        repos=SimpleNamespace(),
    )
    assert recording_service.calls[0]["organization_id"] == "org-1"


async def test_legacy_create_refuses_a_stale_payload_and_a_viewer(recording_service):
    with pytest.raises(Exception):  # pydantic refuses the retired field names
        legacy.LegacyScheduleCreate(
            name="A",
            reporting_year=2025,
            frequency="daily",
            recipients=["a@b.com"],
            day_of_week=2,
        )

    with pytest.raises(HTTPException) as excinfo:
        await legacy.create_report_schedule(
            schedule_data=legacy.LegacyScheduleCreate(
                name="A", reporting_year=2025, frequency="annual", recipients=["a@b.com"]
            ),
            response=Response(),
            current_user=org_owner(role="org_viewer", role_name="viewer"),
            repos=SimpleNamespace(),
        )
    assert excinfo.value.status_code == 403
    assert recording_service.calls == []


async def test_legacy_delete_reports_missing_schedules_as_404(recording_service):
    recording_service.deleted = False
    with pytest.raises(HTTPException) as excinfo:
        await legacy.delete_report_schedule(
            schedule_id="s-1",
            response=Response(),
            organization_id=None,
            current_user=org_owner(),
            repos=SimpleNamespace(),
        )
    assert excinfo.value.status_code == 404


class RecordingShareService:
    """Stand-in for the canonical share service."""

    calls: list[dict] = []
    received_calls: list[dict] = []
    shares: list[dict] = []

    def __init__(self, repos) -> None:
        self._repos = repos

    async def share(self, **kwargs):
        RecordingShareService.calls.append(kwargs)
        return RecordingShareService.shares

    async def received(self, *, user_id, email):
        RecordingShareService.received_calls.append({"user_id": user_id, "email": email})
        return RecordingShareService.shares


class FakeReportsRepo:
    def __init__(self, report) -> None:
        self._report = report

    async def get_full(self, report_id):
        return self._report


@pytest.fixture
def recording_share_service(monkeypatch):
    RecordingShareService.calls = []
    RecordingShareService.received_calls = []
    RecordingShareService.shares = [
        {
            "id": str(uuid.uuid4()),
            "organization_id": "org-1",
            "report_id": "report-1",
            "report_version_id": "version-1",
            "permission": "view",
            "recipient_user_id": None,
            "recipient_email": "reader@example.com",
            "created_by": "user-1",
            "created_at": datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            "expires_at": None,
            "revoked_at": None,
            "revoked_by": None,
            "revocation_reason": None,
            "access_count": 0,
            "last_accessed_at": None,
            "is_active": True,
        }
    ]
    monkeypatch.setattr(legacy, "ReportShareService", RecordingShareService)
    return RecordingShareService


async def test_legacy_share_delegates_to_the_canonical_service(recording_share_service):
    response = Response()
    body = await legacy.share_report(
        report_id="report-1",
        share_data=legacy.LegacyShareCreate(
            shared_with=["Reader@Example.com"], permission="download"
        ),
        response=response,
        current_user=org_owner(),
        repos=SimpleNamespace(
            reports=FakeReportsRepo({"id": "report-1", "organization_id": "org-1"})
        ),
    )

    call = recording_share_service.calls[0]
    assert call["organization_id"] == "org-1"
    assert call["report_id"] == "report-1"
    assert call["recipients"] == ["Reader@Example.com"]
    assert call["permission"] == "download"
    assert call["version_number"] is None
    assert body["shared_with"] == [recording_share_service.shares[0]["id"]]
    assert body["shares"][0]["is_active"] is True
    assert response.headers["Deprecation"] == "true"


async def test_legacy_share_refuses_a_mismatched_or_unknown_report(
    recording_share_service,
):
    with pytest.raises(HTTPException) as excinfo:
        await legacy.share_report(
            report_id="report-1",
            share_data=legacy.LegacyShareCreate(
                report_id="report-2", shared_with=["r@example.com"]
            ),
            response=Response(),
            current_user=org_owner(),
            repos=SimpleNamespace(),
        )
    assert excinfo.value.status_code == 422

    with pytest.raises(HTTPException) as excinfo:
        await legacy.share_report(
            report_id="report-1",
            share_data=legacy.LegacyShareCreate(shared_with=["r@example.com"]),
            response=Response(),
            current_user=org_owner(),
            repos=SimpleNamespace(reports=FakeReportsRepo(None)),
        )
    assert excinfo.value.status_code == 404
    assert recording_share_service.calls == []


async def test_legacy_shared_lists_what_the_canonical_register_gives_the_caller(
    recording_share_service,
):
    response = Response()
    body = await legacy.get_shared_reports(
        response=response, current_user=org_owner(), repos=SimpleNamespace()
    )

    assert recording_share_service.received_calls == [
        {"user_id": "user-1", "email": "owner@example.com"}
    ]
    assert body["total"] == 1
    assert body["shares"][0]["id"] == recording_share_service.shares[0]["id"]
    assert response.headers["Deprecation"] == "true"


# ---------------------------------------------------------------------------
# Canonical surface: registration, authority, vocabulary drift
# ---------------------------------------------------------------------------
def test_the_canonical_schedule_and_share_routes_are_registered():
    from api import v3_reports

    paths = flatten_router_paths(v3_reports.router)
    for path in (
        "/api/v3/reports/schedules",
        "/api/v3/reports/schedules/frequencies",
        "/api/v3/reports/schedules/{schedule_id}",
        "/api/v3/reports/schedules/{schedule_id}/runs",
        "/api/v3/reports/schedules/{schedule_id}/pause",
        "/api/v3/reports/schedules/{schedule_id}/resume",
        "/api/v3/reports/{report_id}/shares",
        "/api/v3/reports/shares/{share_id}/revoke",
        "/api/v3/reports/shares/{share_id}/access-history",
        "/api/v3/reports/shares/received",
    ):
        assert path in paths, path


def test_schedule_report_types_stay_within_what_the_engine_supports():
    """Drift guard: a schedule may only claim a report the engine produces."""
    from api import v3_reports
    from domain.report_schedule import SCHEDULE_REPORT_TYPES

    assert set(SCHEDULE_REPORT_TYPES) <= set(v3_reports.SUPPORTED_REPORT_TYPES)


@pytest.mark.parametrize(
    "user, expected",
    [
        (org_owner(), None),
        (org_owner(role="org_admin", role_name="admin"), None),
        (org_owner(role="org_member", role_name="member"), 403),
        (org_owner(role="org_viewer", role_name="viewer"), 403),
        # Processing Entity staff are not customer-organisation authorities.
        (org_owner(is_staff=True, entity_id="entity-1"), 403),
        # CarbonTally internal staff are not customer-organisation authorities.
        (org_owner(is_staff=True, entity_id=None), 403),
        # A member of a different organisation cannot act on this organisation.
        (org_owner(organization_id="org-2"), 403),
    ],
)
async def test_org_authority_is_enforced_server_side(user, expected):
    from api.v3_reports import authorize_org_authority

    if expected is None:
        authorize_org_authority(user, "org-1", "create_schedule")
    else:
        with pytest.raises(HTTPException) as excinfo:
            authorize_org_authority(user, "org-1", "create_schedule")
        assert excinfo.value.status_code == expected
