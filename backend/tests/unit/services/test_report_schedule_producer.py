"""CT-IMPLEMENT-03 (PD-2) — canonical scheduled-report producer tests.

The producer's job is to turn one due slot into a canonical report + version
through the authoritative engine, and to persist the real failure when the engine
refuses. These tests hold it to that contract with fake repositories and a fake
engine, so the assertions are about the *sequence and the artefacts*, not about
report content (the engine has its own suite).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from types import SimpleNamespace

import pytest

from services.report_schedule_producer import CanonicalReportProducer

DUE = datetime(2026, 4, 10, 6, 0, tzinfo=timezone.utc)


class FakeReports:
    """``report_generation_queue`` stand-in (QUEUED → GENERATING → READY/FAILED)."""

    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.generating: list[str] = []
        self.failed: list[tuple[str, str]] = []

    async def create_generation_request(
        self,
        org_id,
        report_type,
        year,
        template_id,
        created_by=None,
        report_name=None,
    ):
        row_id = str(uuid.uuid4())
        self.requests.append(
            {
                "id": row_id,
                "organization_id": org_id,
                "report_type": report_type,
                "reporting_year": year,
                "report_name": report_name,
                "created_by": created_by,
            }
        )
        return SimpleNamespace(id=row_id)

    async def mark_generating(self, report_id, user_id=None):
        self.generating.append(report_id)
        return {"id": report_id}

    async def mark_failed(self, report_id, *, error_log=None, user_id=None):
        self.failed.append((report_id, error_log or ""))
        return {"id": report_id}


class FakeVersions:
    """``report_versions`` stand-in (one version per report)."""

    def __init__(self) -> None:
        self.created: list[dict] = []

    async def next_version_number(self, report_id):
        return 1

    async def create(
        self,
        report_id,
        *,
        version_number,
        content=None,
        file_url="",
        file_name=None,
        created_by=None,
        notes=None,
        change_summary=None,
        is_current=True,
        status="DRAFT",
    ):
        row = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "version_number": version_number,
            "file_url": file_url,
            "change_summary": change_summary,
            "is_current": is_current,
            "status": status,
        }
        self.created.append(row)
        return row


class FakeEngine:
    """The authoritative report engine, reduced to its contract."""

    def __init__(self, *, error: Exception | None = None, page_count: int = 12) -> None:
        self.error = error
        self.page_count = page_count
        self.calls: list[tuple[object, str | None]] = []

    async def generate(self, request, report_id=None):
        self.calls.append((request, report_id))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            report=SimpleNamespace(id=report_id, storage_url="storage://report.json"),
            content=SimpleNamespace(to_dict=lambda: {"page_count": self.page_count}),
        )


def make_producer(*, error=None):
    reports, versions, engine = FakeReports(), FakeVersions(), FakeEngine(error=error)
    repos = SimpleNamespace(reports=reports, report_versions=versions)
    return CanonicalReportProducer(repos, engine), reports, versions, engine


def make_schedule(**overrides):
    values = {
        "id": str(uuid.uuid4()),
        "organization_id": str(uuid.uuid4()),
        "name": "Monthly pack",
        "report_type": "annual",
        "reporting_year": 2025,
        "frequency": "monthly",
        "run_time": time(7, 0),
        "timezone": "Europe/London",
        "next_run_at": DUE,
        "period_start": date(2025, 1, 1),
        "period_end": date(2025, 12, 31),
    }
    values.update(overrides)
    from domain.report_schedule import ScheduleDefinition

    return ScheduleDefinition.from_row(values)


async def test_success_produces_a_canonical_report_and_version():
    producer, reports, versions, engine = make_producer()

    produced = await producer(make_schedule(), scheduled_for=DUE)

    assert produced is not None
    assert produced.report_id == reports.requests[0]["id"]
    assert produced.report_version_id == versions.created[0]["id"]
    # The queue row is created first, then moved to GENERATING, then completed by
    # the engine against that same row — the V3 reporting lifecycle.
    assert reports.generating == [produced.report_id]
    assert engine.calls[0][1] == produced.report_id
    assert reports.failed == []
    assert produced.result_summary == {
        "report_type": "annual",
        "reporting_year": 2025,
        "version_number": 1,
        "page_count": 12,
    }


async def test_the_request_carries_the_schedule_configuration():
    producer, reports, _, engine = make_producer()
    schedule = make_schedule()

    await producer(schedule, scheduled_for=DUE)

    request = engine.calls[0][0]
    assert request.organization_id == schedule.organization_id
    assert request.report_type == "annual"
    assert request.reporting_year == 2025
    assert request.options["schedule_id"] == schedule.id
    assert request.options["scheduled"] is True
    assert request.options["period_start"] == "2025-01-01"
    assert request.options["period_end"] == "2025-12-31"
    assert reports.requests[0]["report_name"].startswith("Monthly pack")


async def test_a_failed_generation_is_re_raised_and_persisted_as_failed():
    producer, reports, versions, _ = make_producer(error=RuntimeError("engine exploded"))

    with pytest.raises(RuntimeError, match="engine exploded"):
        await producer(make_schedule(), scheduled_for=DUE)

    # The queue row must not claim to be generating while the run says failed.
    assert reports.failed == [(reports.requests[0]["id"], "engine exploded")]
    assert versions.created == []


async def test_a_failure_to_mark_the_queue_row_failed_never_masks_the_original():
    class ExplodingReports(FakeReports):
        async def mark_failed(self, report_id, *, error_log=None, user_id=None):
            raise RuntimeError("mark_failed also failed")

    reports = ExplodingReports()
    engine = FakeEngine(error=RuntimeError("engine exploded"))
    producer = CanonicalReportProducer(
        SimpleNamespace(reports=reports, report_versions=FakeVersions()), engine
    )

    with pytest.raises(RuntimeError, match="engine exploded"):
        await producer(make_schedule(), scheduled_for=DUE)


async def test_the_producer_never_returns_none():
    """A "skip" is a product decision that has not been ratified.

    The runner records a producer that produces nothing as a FAILURE, so the
    producer must either produce a canonical report or raise — never return None
    (which would be a silent, invented skip policy).
    """
    producer, _, _, _ = make_producer()
    result = await producer(make_schedule(), scheduled_for=DUE)
    assert result is not None


def test_producer_requires_repos_and_engine():
    with pytest.raises(ValueError):
        CanonicalReportProducer(None, FakeEngine())
    with pytest.raises(ValueError):
        CanonicalReportProducer(SimpleNamespace(), None)
