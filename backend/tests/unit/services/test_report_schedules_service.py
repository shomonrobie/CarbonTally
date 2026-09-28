"""CT-IMPLEMENT-03 (PD-2) — canonical report-schedule service tests.

The service is verified against an in-memory store that reproduces the canonical
table's semantics (a definition row with persisted state, a tenant-scoped read, a
pause/resume update and a delete), so the assertions are about *behaviour* —
vocabulary, due-time arithmetic, audit correlation, tenant isolation — not about
a database driver.
"""
from __future__ import annotations

import pathlib
import uuid
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from domain.report_schedule import FREQUENCIES, LEGACY_UNSUPPORTED_FREQUENCIES
from services.report_schedules import (
    AUDIT_SCHEDULE_CREATED,
    AUDIT_SCHEDULE_DELETED,
    AUDIT_SCHEDULE_PAUSED,
    AUDIT_SCHEDULE_RESUMED,
    ENTITY_SCHEDULE,
    ReportScheduleService,
    ScheduleInUseError,
    ScheduleValidationError,
    build_audit_sink,
    canonical_frequencies,
)

NOW = datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc)


class FakeScheduleStore:
    """In-memory ``report_schedule_definitions`` with the real read scoping."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.runs: list[dict] = []

    async def create(self, **kwargs) -> dict:
        row = {
            "id": str(uuid.uuid4()),
            "organization_id": kwargs["organization_id"],
            "name": kwargs["name"],
            "report_type": kwargs["report_type"],
            "reporting_year": kwargs["reporting_year"],
            "period_start": kwargs.get("period_start"),
            "period_end": kwargs.get("period_end"),
            "recipients": list(kwargs["recipients"]),
            "frequency": kwargs["frequency"],
            "run_time": kwargs["run_time"],
            "timezone": kwargs["timezone_name"],
            "is_active": kwargs.get("is_active", True),
            "paused_at": None,
            "created_by": kwargs["created_by"],
            "created_at": NOW,
            "updated_at": NOW,
            "next_run_at": kwargs["next_run_at"],
            "last_run_at": None,
            "last_result": None,
            "last_error": None,
            "failure_count": 0,
            "retry_policy": dict(kwargs.get("retry_policy") or {}),
        }
        self.rows[row["id"]] = row
        return row

    async def get_for_org(self, id: str, organization_id: str):
        row = self.rows.get(id)
        if row is None or row["organization_id"] != organization_id:
            return None
        return row

    async def list_for_org(self, organization_id, *, limit=100, offset=0, is_active=None):
        rows = [
            r
            for r in self.rows.values()
            if r["organization_id"] == organization_id
            and (is_active is None or r["is_active"] == is_active)
        ]
        return rows[offset : offset + limit]

    async def count_for_org(self, organization_id) -> int:
        return len(
            [r for r in self.rows.values() if r["organization_id"] == organization_id]
        )

    async def set_active(self, id, *, is_active, next_run_at, paused_at):
        row = self.rows.get(id)
        if row is None:
            return None
        row.update(
            is_active=is_active, next_run_at=next_run_at, paused_at=paused_at
        )
        return row

    async def delete(self, id) -> bool:
        return self.rows.pop(id, None) is not None

    async def has_runs(self, schedule_id) -> bool:
        return any(r["schedule_id"] == schedule_id for r in self.runs)

    async def list_runs(self, schedule_id, *, limit=50):
        return [r for r in self.runs if r["schedule_id"] == schedule_id][:limit]


class FakeAudit:
    """Canonical audit sink stand-in (records the entries it is given)."""

    def __init__(self) -> None:
        self.entries: list = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry


def make_service(*, now: datetime = NOW):
    store = FakeScheduleStore()
    audit = FakeAudit()
    repos = SimpleNamespace(report_schedules=store, audit=audit)
    service = ReportScheduleService(repos, clock=lambda: now)
    return service, store, audit


async def create_schedule(service, **overrides):
    payload = {
        "name": "Annual report",
        "report_type": "annual",
        "reporting_year": 2025,
        "frequency": "monthly",
        "run_time": time(7, 0),
        "recipients": ["owner@example.com"],
        "timezone_name": "Europe/London",
    }
    payload.update(overrides)
    return await service.create("org-1", actor="user-1", **payload)


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------
async def test_create_persists_the_canonical_row_and_computes_the_due_time():
    service, store, audit = make_service()
    row = await create_schedule(service)

    assert row["organization_id"] == "org-1"
    assert row["frequency"] == "monthly"
    assert row["report_type"] == "annual"
    assert row["reporting_year"] == 2025
    assert row["created_by"] == "user-1"
    # The next due time is a real future instant at the configured LOCAL time in
    # the schedule's own timezone — not "now" and not the current instant.
    assert row["next_run_at"] > NOW
    local = row["next_run_at"].astimezone(ZoneInfo("Europe/London"))
    assert (local.hour, local.minute) == (7, 0)
    assert local.date() == date(2026, 4, 10)
    assert len(store.rows) == 1


async def test_create_audits_with_correlation_id_equal_to_the_schedule_id():
    service, _, audit = make_service()
    row = await create_schedule(service)

    assert len(audit.entries) == 1
    entry = audit.entries[0]
    assert entry.action == AUDIT_SCHEDULE_CREATED
    assert entry.correlation_id == row["id"]
    assert entry.entity_type == ENTITY_SCHEDULE
    assert entry.entity_id == row["id"]
    assert entry.actor == "user-1"
    assert entry.organization_id == "org-1"


async def test_create_normalises_recipients_to_explicit_user_or_email():
    service, _, _ = make_service()
    row = await create_schedule(
        service, recipients=["Owner@Example.COM", "11111111-1111-4111-8111-111111111111"]
    )

    assert row["recipients"] == [
        {"user_id": None, "email": "owner@example.com"},
        {"user_id": "11111111-1111-4111-8111-111111111111", "email": None},
    ]


@pytest.mark.parametrize("frequency", ["daily", "hourly", "", "WEEKLY"])
async def test_create_refuses_a_frequency_the_canonical_check_rejects(frequency):
    service, store, audit = make_service()
    with pytest.raises(ScheduleValidationError) as excinfo:
        await create_schedule(service, frequency=frequency)

    message = str(excinfo.value)
    assert repr(frequency) in message
    assert "canonical frequencies" in message
    assert not store.rows, "nothing may be persisted for an invalid frequency"
    assert not audit.entries


async def test_create_refuses_daily_with_the_retired_surface_explanation():
    service, _, _ = make_service()
    with pytest.raises(ScheduleValidationError) as excinfo:
        await create_schedule(service, frequency="daily")

    message = str(excinfo.value)
    assert "daily" in message
    assert LEGACY_UNSUPPORTED_FREQUENCIES[0] in message
    assert "not a canonical frequency" in message


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "   "},
        {"report_type": "summary"},
        {"reporting_year": 1989},
        {"reporting_year": 2101},
        {"timezone_name": "Europe/Nowhere"},
        {"run_time": "not-a-time"},
        {"recipients": []},
        {"period_start": date(2025, 6, 1), "period_end": date(2025, 5, 1)},
    ],
)
async def test_create_refuses_a_configuration_the_schema_would_reject(overrides):
    service, store, _ = make_service()
    with pytest.raises(ScheduleValidationError):
        await create_schedule(service, **overrides)
    assert not store.rows


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
async def test_list_reports_total_and_the_canonical_frequencies():
    service, _, _ = make_service()
    await create_schedule(service)
    page = await service.list_schedules("org-1")

    assert page["total"] == 1
    assert len(page["schedules"]) == 1
    assert [f["value"] for f in page["frequencies"]] == list(FREQUENCIES)
    assert "daily" not in [f["value"] for f in page["frequencies"]]


async def test_tenant_isolation_get_and_runs_are_organisation_scoped():
    service, _, _ = make_service()
    row = await create_schedule(service)

    assert await service.get("org-2", row["id"]) is None
    assert await service.runs("org-2", row["id"]) is None
    assert await service.get("org-1", row["id"]) is not None


# ---------------------------------------------------------------------------
# Pause / resume / delete
# ---------------------------------------------------------------------------
async def test_pause_keeps_the_due_time_and_is_audited():
    service, _, audit = make_service()
    row = await create_schedule(service)
    due = row["next_run_at"]

    paused = await service.pause("org-1", row["id"], actor="user-1")

    assert paused["is_active"] is False
    assert paused["paused_at"] == NOW
    assert paused["next_run_at"] == due, "pausing must not destroy the due time"
    assert [e.action for e in audit.entries] == [
        AUDIT_SCHEDULE_CREATED,
        AUDIT_SCHEDULE_PAUSED,
    ]
    assert audit.entries[-1].correlation_id == row["id"]


async def test_resume_keeps_a_future_due_time_and_recomputes_a_past_one():
    service, store, audit = make_service()
    row = await create_schedule(service)
    await service.pause("org-1", row["id"], actor="user-1")

    resumed = await service.resume("org-1", row["id"], actor="user-1")
    assert resumed["is_active"] is True
    assert resumed["paused_at"] is None
    assert resumed["next_run_at"] == row["next_run_at"], "a pause is not a reschedule"

    # An overdue schedule resumes at its NEXT real period boundary, not as an
    # immediate catch-up run.
    store.rows[row["id"]]["next_run_at"] = NOW - timedelta(days=90)
    await service.pause("org-1", row["id"], actor="user-1")
    resumed = await service.resume("org-1", row["id"], actor="user-1")

    assert resumed["next_run_at"] > NOW
    assert [e.action for e in audit.entries][-1] == AUDIT_SCHEDULE_RESUMED


async def test_delete_is_scoped_audited_and_reports_unknown_schedules():
    service, _, audit = make_service()
    row = await create_schedule(service)

    assert await service.delete("org-2", row["id"], actor="user-1") is False
    assert await service.delete("org-1", row["id"], actor="user-1") is True
    assert await service.delete("org-1", row["id"], actor="user-1") is False
    assert [e.action for e in audit.entries][-1] == AUDIT_SCHEDULE_DELETED
    assert audit.entries[-1].correlation_id == row["id"]


async def test_delete_refuses_a_schedule_that_has_executed():
    """Run history is immutable, so a schedule that ran cannot be deleted."""
    service, store, audit = make_service()
    row = await create_schedule(service)
    store.runs.append(
        {
            "id": str(uuid.uuid4()),
            "schedule_id": row["id"],
            "organization_id": "org-1",
            "scheduled_for": NOW,
            "attempt": 1,
            "status": "succeeded",
        }
    )

    with pytest.raises(ScheduleInUseError) as excinfo:
        await service.delete("org-1", row["id"], actor="user-1")

    assert "pause it" in str(excinfo.value)
    assert row["id"] in store.rows, "the schedule must survive the refusal"
    assert [e.action for e in audit.entries] == [AUDIT_SCHEDULE_CREATED]


# ---------------------------------------------------------------------------
# Vocabulary and the runner's audit sink
# ---------------------------------------------------------------------------
def test_canonical_frequencies_advertise_only_persistable_values():
    values = [item["value"] for item in canonical_frequencies()]
    assert values == list(FREQUENCIES)
    for legacy in LEGACY_UNSUPPORTED_FREQUENCIES:
        assert legacy not in values


async def test_audit_sink_records_runner_outcomes_against_the_schedule():
    audit = FakeAudit()
    repos = SimpleNamespace(audit=audit)
    sink = build_audit_sink(repos)

    schedule_id = str(uuid.uuid4())
    await sink(
        "report_schedule_run_succeeded",
        {
            "correlation_id": schedule_id,
            "organization_id": "org-1",
            "actor": "system",
            "actor_type": "system",
            "report_schedule_id": schedule_id,
            "status": "succeeded",
            "report_id": "report-1",
        },
    )
    entry = audit.entries[0]
    assert entry.correlation_id == schedule_id
    assert entry.entity_id == schedule_id
    assert entry.entity_type == ENTITY_SCHEDULE
    assert entry.action == "report_schedule_run_succeeded"
    assert entry.changed_fields["report_id"] == "report-1"
    assert "organization_id" not in entry.changed_fields

    await sink("report_schedule_run_failed", {"report_schedule_id": schedule_id})
    assert audit.entries[1].outcome == "failure"


def test_service_module_never_reaches_a_retired_table():
    """The canonical service must not name a retired table for ACCESS.

    (The module docstring explains what was retired; that is prose, not a query.
    The runtime-wide regression assertion lives in
    ``tests/unit/routes/test_ct03_legacy_canonical_delegation.py``.)
    """
    source = pathlib.Path(
        "/home/shomonrobie/ct_93d5cdd/backend/services/report_schedules.py"
    ).read_text()
    for pattern in ("from_(", "FROM report_", "INTO report_", "DELETE FROM"):
        assert pattern not in source
