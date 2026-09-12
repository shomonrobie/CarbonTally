"""Integration tests for ReportVersionsRepository (existing report_versions table)."""
from __future__ import annotations

import asyncpg
import pytest

from data.report_versions import ReportVersionsRepository
from data.reports import ReportsRepository
from tests.integration.conftest import make_org

pytestmark = pytest.mark.asyncio


async def test_next_version_number_starts_at_one(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    org_id = await make_org(pool)
    reports = ReportsRepository(pool)
    report = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    assert await repo.next_version_number(report.id) == 1


async def test_create_and_roundtrip_version(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    org_id = await make_org(pool)
    reports = ReportsRepository(pool)
    report = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )

    version = await repo.create(
        report.id,
        version_number=1,
        content={"totals": {"total_co2e_kg": "183.000000"}},
        file_url="storage/reports/x.json",
        created_by="user-1",
        change_summary="Generated annual report for 2025",
        is_current=True,
    )
    assert version["report_id"] == report.id
    assert version["version_number"] == 1
    assert version["is_current"] is True

    rows = await repo.list_for_report(report.id)
    assert len(rows) == 1
    assert rows[0]["content"]["totals"]["total_co2e_kg"] == "183.000000"

    current = await repo.get_current(report.id)
    assert current is not None
    assert current["version_number"] == 1


async def test_version_numbers_increment(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    org_id = await make_org(pool)
    reports = ReportsRepository(pool)
    report = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    await repo.create(report.id, version_number=1, is_current=False)
    await repo.create(report.id, version_number=2, is_current=True)

    assert await repo.next_version_number(report.id) == 3
    current = await repo.get_current(report.id)
    assert current["version_number"] == 2
    assert len(await repo.list_for_report(report.id)) == 2


# ---------------------------------------------------------------------------
# Phase 8 S1-A — the single-current-version invariant
# ---------------------------------------------------------------------------


def _current_numbers(versions: list[dict]) -> list[int]:
    """Version numbers flagged current (the invariant probe)."""
    return [v["version_number"] for v in versions if v["is_current"]]


async def _cleanup_report(pool: asyncpg.Pool, report_id: str) -> None:
    """Remove only the rows this test created (no leaked report/version state)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.report_versions WHERE report_id = $1", report_id
        )
        await conn.execute(
            "DELETE FROM public.report_generation_queue WHERE id = $1", report_id
        )


async def test_create_current_version_demotes_previous_version(
    pool: asyncpg.Pool,
) -> None:
    """Creating a second current version leaves exactly one current version.

    S1-A regression, exercised through the real ``ReportVersionsRepository``
    (never a re-implementation of the logic): the create path must demote the
    previous current version(s) for the same report in the same transaction.
    """
    repo = ReportVersionsRepository(pool)
    reports = ReportsRepository(pool)
    org_id = await make_org(pool)
    report = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    try:
        first = await repo.create(
            report.id, version_number=1, content={"v": 1}, is_current=True
        )
        assert first["is_current"] is True
        assert _current_numbers(await repo.list_for_report(report.id)) == [1]

        second = await repo.create(
            report.id, version_number=2, content={"v": 2}, is_current=True
        )
        assert second["is_current"] is True

        versions = await repo.list_for_report(report.id)
        assert [v["version_number"] for v in versions] == [2, 1]
        # Exactly one current version, and it is the newest.
        assert _current_numbers(versions) == [2]
        assert versions[0]["is_current"] is True   # v2 is current
        assert versions[1]["is_current"] is False  # v1 was demoted

        # The single-row and batch read paths agree with ``is_current``.
        current = await repo.get_current(report.id)
        assert current is not None
        assert current["version_number"] == 2
        batch = await repo.current_by_reports([report.id])
        assert batch[report.id]["version_number"] == 2
    finally:
        await _cleanup_report(pool, report.id)


async def test_create_non_current_version_leaves_current_intact(
    pool: asyncpg.Pool,
) -> None:
    """A non-current create never disturbs the existing current version."""
    repo = ReportVersionsRepository(pool)
    reports = ReportsRepository(pool)
    org_id = await make_org(pool)
    report = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    try:
        await repo.create(report.id, version_number=1, is_current=True)
        await repo.create(report.id, version_number=2, is_current=False)

        versions = await repo.list_for_report(report.id)
        assert _current_numbers(versions) == [1]
        current = await repo.get_current(report.id)
        assert current is not None and current["version_number"] == 1
    finally:
        await _cleanup_report(pool, report.id)


async def test_current_by_reports_returns_absent_for_no_current_version(
    pool: asyncpg.Pool,
) -> None:
    """The batch read reports only genuine current versions (absence, no 1)."""
    repo = ReportVersionsRepository(pool)
    reports = ReportsRepository(pool)
    org_id = await make_org(pool)
    with_version = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    without_version = await reports.create_generation_request(
        org_id=org_id, report_type="annual", year=2024, template_id=None
    )
    try:
        await repo.create(with_version.id, version_number=1, is_current=True)
        batch = await repo.current_by_reports([with_version.id, without_version.id])

        assert set(batch) == {with_version.id}
        assert batch[with_version.id]["version_number"] == 1
        # A report with no current version is absent — never version 1.
        assert without_version.id not in batch
        # Empty input does no work and fabricates nothing.
        assert await repo.current_by_reports([]) == {}
    finally:
        await _cleanup_report(pool, with_version.id)
        await _cleanup_report(pool, without_version.id)
