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
