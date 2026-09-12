"""Integration tests for the Phase 8 S3 report-version lifecycle persistence.

Exercises the real ``ReportVersionsRepository`` (and the real CHECK constraint)
against the dedicated integration test database. Every test cleans up only the
rows it created.
"""
from __future__ import annotations

import asyncpg
import pytest

from data.report_versions import ReportVersionsRepository
from data.reports import ReportsRepository
from domain.report_lifecycle import APPROVED, DRAFT, FINAL, REVIEWED
from tests.integration.conftest import make_org

pytestmark = pytest.mark.asyncio


async def _make_report(pool: asyncpg.Pool):
    org_id = await make_org(pool)
    return await ReportsRepository(pool).create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )


async def _cleanup(pool: asyncpg.Pool, report_id: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.report_versions WHERE report_id = $1", report_id
        )
        await conn.execute(
            "DELETE FROM public.report_generation_queue WHERE id = $1", report_id
        )


async def test_new_version_defaults_to_draft(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        version = await repo.create(
            report.id, version_number=1, content={"v": 1}, is_current=True
        )
        assert version["status"] == DRAFT
    finally:
        await _cleanup(pool, report.id)


async def test_guarded_status_transition_updates_only_expected_state(
    pool: asyncpg.Pool,
) -> None:
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        v = await repo.create(report.id, version_number=1, is_current=True)

        # Wrong expected state → the guard matches zero rows.
        assert (
            await repo.set_status(
                report.id, v["id"], expected_status=REVIEWED, new_status=APPROVED
            )
            is None
        )

        moved = await repo.set_status(
            report.id, v["id"], expected_status=DRAFT, new_status=REVIEWED
        )
        assert moved is not None and moved["status"] == REVIEWED
        assert moved["id"] == v["id"] and moved["version_number"] == 1

        # Stale repeat of the original guard is now a no-op.
        assert (
            await repo.set_status(
                report.id, v["id"], expected_status=DRAFT, new_status=REVIEWED
            )
            is None
        )
        stored = await repo.get_by_number(report.id, 1)
        assert stored is not None and stored["status"] == REVIEWED
    finally:
        await _cleanup(pool, report.id)


async def test_version_state_is_isolated_per_report(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    report_a = await _make_report(pool)
    report_b = await _make_report(pool)
    try:
        await repo.create(
            report_a.id, version_number=1, is_current=True, status=FINAL
        )
        await repo.create(
            report_b.id, version_number=1, is_current=True, status=DRAFT
        )
        a1 = await repo.get_by_number(report_a.id, 1)
        b1 = await repo.get_by_number(report_b.id, 1)
        assert a1["status"] == FINAL
        assert b1["status"] == DRAFT
        assert await repo.get_by_number(report_a.id, 2) is None
    finally:
        await _cleanup(pool, report_a.id)
        await _cleanup(pool, report_b.id)


async def test_unratified_status_is_rejected_before_write(
    pool: asyncpg.Pool,
) -> None:
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        with pytest.raises(ValueError):
            await repo.create(
                report.id,
                version_number=1,
                is_current=True,
                status="VERIFIED",  # no assurance state exists
            )
        assert await repo.list_for_report(report.id) == []
    finally:
        await _cleanup(pool, report.id)


async def test_check_constraint_blocks_unratified_state(
    pool: asyncpg.Pool,
) -> None:
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        await repo.create(report.id, version_number=1, is_current=True)
        async with pool.acquire() as conn:
            with pytest.raises(asyncpg.exceptions.CheckViolationError):
                await conn.execute(
                    "UPDATE public.report_versions SET status = 'VERIFIED' "
                    "WHERE report_id = $1",
                    report.id,
                )
        stored = await repo.get_by_number(report.id, 1)
        assert stored["status"] == DRAFT
    finally:
        await _cleanup(pool, report.id)


async def test_final_is_terminal_for_the_guard(pool: asyncpg.Pool) -> None:
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        v = await repo.create(
            report.id, version_number=1, is_current=True, status=APPROVED
        )
        final = await repo.set_status(
            report.id, v["id"], expected_status=APPROVED, new_status=FINAL
        )
        assert final is not None and final["status"] == FINAL

        # The version's content is untouched and no transition leaves FINAL.
        assert final["content"] == v["content"]
        assert (
            await repo.set_status(
                report.id, v["id"], expected_status=APPROVED, new_status=FINAL
            )
            is None
        )
        stored = await repo.get_by_number(report.id, 1)
        assert stored["status"] == FINAL
    finally:
        await _cleanup(pool, report.id)
