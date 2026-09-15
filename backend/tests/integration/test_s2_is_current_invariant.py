"""`…046` (S2) — the one-current-version-per-report invariant.

Locks the integrity guarantee added by
``supabase/migrations/20260921000000_p8_s2_is_current_single_valued.sql``:

    at most ONE row with ``is_current = true`` per ``report_id``

Everything runs inside a transaction that is **rolled back**, so the suite leaves
no residue in the integration database (AGENTS §55). It skips — never fails —
when the report tables are not provisioned.
"""
from __future__ import annotations

import asyncpg
import pytest

INDEX_NAME = "report_versions_one_current_per_report"


async def _require_report_schema(pool: asyncpg.Pool) -> None:
    for table in ("report_versions", "report_generation_queue"):
        present = await pool.fetchval(f"SELECT to_regclass('public.{table}') IS NOT NULL")
        if not present:
            pytest.skip(f"{table} is not provisioned in this integration database")


async def _new_report(conn: asyncpg.Connection) -> str:
    """An isolated report for an existing organisation (created inside the tx)."""
    report_id = await conn.fetchval(
        "INSERT INTO public.report_generation_queue "
        "(organization_id, report_type, reporting_year) "
        "SELECT id, 'ANNUAL_CARBON', 2025 FROM public.organizations LIMIT 1 "
        "RETURNING id"
    )
    if report_id is None:
        pytest.skip("no organisation is available to attach a report to")
    return str(report_id)


async def test_a_second_current_version_for_the_same_report_is_rejected(
    pool: asyncpg.Pool,
) -> None:
    await _require_report_schema(pool)
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        try:
            report_id = await _new_report(conn)
            first = await conn.fetchval(
                "INSERT INTO public.report_versions (report_id, version_number, status, is_current) "
                "VALUES ($1, 1, 'DRAFT', TRUE) RETURNING id",
                report_id,
            )
            assert first is not None

            # A statement that violates the index aborts the whole transaction, so the
            # expected failure is isolated in a SAVEPOINT (asyncpg nested transaction).
            savepoint = conn.transaction()
            await savepoint.start()
            try:
                with pytest.raises(asyncpg.exceptions.UniqueViolationError) as excinfo:
                    await conn.fetchval(
                        "INSERT INTO public.report_versions "
                        "(report_id, version_number, status, is_current) "
                        "VALUES ($1, 2, 'DRAFT', TRUE) RETURNING id",
                        report_id,
                    )
                # The rejection must come from OUR index, not another constraint.
                assert INDEX_NAME in str(excinfo.value)
            finally:
                await savepoint.rollback()

            # A non-current second version is still perfectly legal.
            second = await conn.fetchval(
                "INSERT INTO public.report_versions (report_id, version_number, status, is_current) "
                "VALUES ($1, 2, 'DRAFT', FALSE) RETURNING id",
                report_id,
            )
            assert second is not None
        finally:
            await tx.rollback()


async def test_a_different_report_may_hold_its_own_current_version(
    pool: asyncpg.Pool,
) -> None:
    await _require_report_schema(pool)
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        try:
            first_report = await _new_report(conn)
            second_report = await _new_report(conn)
            if first_report == second_report:
                pytest.skip("only one report could be created for this probe")

            for report_id in (first_report, second_report):
                created = await conn.fetchval(
                    "INSERT INTO public.report_versions "
                    "(report_id, version_number, status, is_current) "
                    "VALUES ($1, 1, 'DRAFT', TRUE) RETURNING id",
                    report_id,
                )
                assert created is not None

            current = await conn.fetchval(
                "SELECT count(*)::int FROM public.report_versions "
                "WHERE report_id = ANY($1::uuid[]) AND is_current",
                [first_report, second_report],
            )
            assert current == 2, "each report may hold exactly one current version"
        finally:
            await tx.rollback()


async def test_the_invariant_holds_across_the_existing_catalogue(pool: asyncpg.Pool) -> None:
    """Pre-existing data must satisfy the new invariant (no historical violation)."""
    await _require_report_schema(pool)
    violations = await pool.fetchval(
        "SELECT count(*)::int FROM ("
        "  SELECT report_id FROM public.report_versions WHERE is_current "
        "  GROUP BY report_id HAVING count(*) > 1) x"
    )
    assert violations == 0


async def test_the_index_is_partial_and_unique(pool: asyncpg.Pool) -> None:
    """The guarantee is enforced by a partial UNIQUE index on (report_id) WHERE is_current."""
    await _require_report_schema(pool)
    definition = await pool.fetchval(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = 'public' "
        "AND tablename = 'report_versions' AND indexname = $1",
        INDEX_NAME,
    )
    assert definition, f"{INDEX_NAME} is missing — apply the S2 migration"
    assert "UNIQUE" in definition.upper()
    assert "(report_id)" in definition
    assert "WHERE is_current" in definition
