"""Integration tests for ReportsRepository."""
from __future__ import annotations

import asyncpg
import pytest

from data.reports import ReportsRepository
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


async def test_create_generation_request(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    org_id = await make_org(pool)
    report = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    assert report.id
    assert report.report_type == "annual"
    assert report.reporting_year == 2025
    assert report.storage_url == ""
    assert report.file_size_bytes == 0
    assert report.page_count == 0


async def test_complete_generation(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    org_id = await make_org(pool)
    report = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    completed = await repo.complete_generation(
        report.id,
        storage_url="storage/reports/annual-2025.pdf",
        file_size=2048,
        page_count=12,
    )
    assert completed.storage_url == "storage/reports/annual-2025.pdf"
    assert completed.file_size_bytes == 2048
    assert completed.page_count == 12

    fetched = await repo.get(report.id)
    assert fetched is not None
    assert fetched.page_count == 12
    assert fetched.storage_url == "storage/reports/annual-2025.pdf"


async def test_get_by_org(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    org_id = await make_org(pool)
    r1 = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2024, template_id=None
    )
    r2 = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    other = await repo.create_generation_request(
        org_id=await make_org(pool), report_type="annual", year=2025, template_id=None
    )
    ids = {r.id for r in await repo.get_by_org(org_id)}
    assert ids == {r1.id, r2.id}
    assert other.id not in ids


async def test_save_updates_report(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    org_id = await make_org(pool)
    report = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    from dataclasses import replace

    completed = replace(report, storage_url="s3://reports/x.pdf", file_size_bytes=99, page_count=4)
    saved = await repo.save(completed)
    assert saved.storage_url == "s3://reports/x.pdf"
    assert saved.page_count == 4


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    report = await repo.create_generation_request(
        org_id=await make_org(pool), report_type="annual", year=2025, template_id=None
    )
    await repo.delete(report.id)
    assert await repo.get(report.id) is None


async def test_mark_generating(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    report = await repo.create_generation_request(
        org_id=await make_org(pool), report_type="annual", year=2025, template_id=None
    )
    row = await repo.mark_generating(report.id, user_id="user-1")
    assert row is not None
    assert row["status"] == "generating"
    assert row["started_at"] is not None
    assert row["updated_by"] == "user-1"


async def test_mark_failed_persists_error(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    report = await repo.create_generation_request(
        org_id=await make_org(pool), report_type="annual", year=2025, template_id=None
    )
    row = await repo.mark_failed(report.id, error_log="validation failed", user_id="user-1")
    assert row is not None
    assert row["status"] == "failed"
    assert row["error_log"] == "validation failed"
    fetched = await repo.get_full(report.id)
    assert fetched["status"] == "failed"
    assert fetched["error_log"] == "validation failed"


async def test_create_request_records_created_by_and_name(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    report = await repo.create_generation_request(
        org_id=await make_org(pool),
        report_type="annual",
        year=2025,
        template_id=None,
        created_by="user-1",
        report_name="Annual emissions report 2025",
    )
    full = await repo.get_full(report.id)
    assert full is not None
    assert full["created_by"] == "user-1"
    assert full["report_name"] == "Annual emissions report 2025"
    assert full["status"] == "pending"


async def test_list_full_filters_and_counts(pool: asyncpg.Pool) -> None:
    repo = ReportsRepository(pool)
    org_id = await make_org(pool)
    r1 = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2024, template_id=None
    )
    r2 = await repo.create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )
    await repo.complete_generation(r2.id, storage_url="s://x", file_size=10, page_count=3)
    other_org = await make_org(pool)
    await repo.create_generation_request(
        org_id=other_org, report_type="annual", year=2025, template_id=None
    )

    all_rows = await repo.list_full(org_id)
    assert {r["id"] for r in all_rows} == {r1.id, r2.id}

    by_status = await repo.list_full(org_id, status="completed")
    assert [r["id"] for r in by_status] == [r2.id]

    by_year = await repo.list_full(org_id, reporting_year=2024)
    assert [r["id"] for r in by_year] == [r1.id]

    counts = await repo.count_by_status(org_id)
    assert counts["pending"] == 1
    assert counts["completed"] == 1
    assert counts["failed"] == 0
