"""Phase 8 S1/S3 — INDEPENDENT VERIFICATION invariant probes.

Task: ``CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260913-030`` — discharging the
S1/S3 verification asymmetry recorded as finding **F-049-6** (``…049`` §F),
``-023`` §10.6 and ``-023`` §11.1 ("no independent verification evidence for
S1 or S3").

These probes are an *independent* pass, not a re-run of the implementation
suite. Each one targets a property that the ratified sources **assert** but the
implementation suite does **not** directly establish:

======================  ================================================  ================
Probe                   Ratified property                                 Covered before?
======================  ================================================  ================
``IV-S1-1``             the demotion and the insert inside
                        ``ReportVersionsRepository.create`` are ONE
                        transaction (S1-A; spec §7.3 "transactionally
                        enforced")                                          no
``IV-S1-2``             the single-current invariant is also enforced at
                        the **database** layer (S2 partial unique index):
                        duplicates are unreachable, not merely masked       no
``IV-S1-3``             the §7.3 legacy duplicated-``is_current`` scenario
                        — the single and batch read paths agree             no
``IV-S1-4``             ``next_version_number`` is ``MAX+1`` (gaps kept)
                        and independent of ``is_current``                   partly
``IV-S1-5``             ``is_current`` is scoped per report instance        no
``IV-S3-5``             the **column** default (migration, not the Python
                        default) is ``DRAFT``                               no
``IV-S3-6``             the CHECK constraint admits *exactly* the six
                        ratified states                                     partly
``IV-S3-7``             ``status`` is ``NOT NULL``                          no
======================  ================================================  ================

**F-046-1 (programme invariant):** this module belongs to the **destructive**
integration harness — ``tests/integration/conftest.py`` executes
``TRUNCATE … RESTART IDENTITY CASCADE`` against its target. It may therefore
only ever be pointed at a disposable ``ct_*`` clone or the dedicated
``carbontally_test`` database, never at persistent QA, the investor demo or
production. The protected-marker refusal is enforced in ``conftest.py`` and
fails closed before any destructive statement runs.
"""
from __future__ import annotations

import re

import asyncpg
import pytest

from data.report_versions import ReportVersionsRepository
from data.reports import ReportsRepository
from domain.report_lifecycle import DRAFT, VERSION_STATUSES
from tests.integration.conftest import make_org

pytestmark = pytest.mark.asyncio

#: The Phase 8 S2 partial unique index that makes the S1 invariant single-valued
#: at the database layer (migration ``20260921000000_p8_s2_is_current_single_valued``).
_S2_INDEX = "report_versions_one_current_per_report"


async def _make_report(pool: asyncpg.Pool):
    org_id = await make_org(pool)
    return await ReportsRepository(pool).create_generation_request(
        org_id=org_id, report_type="annual", year=2025, template_id=None
    )


async def _cleanup(pool: asyncpg.Pool, *report_ids: str) -> None:
    """Remove only the rows this module created."""
    async with pool.acquire() as conn:
        for report_id in report_ids:
            await conn.execute(
                "DELETE FROM public.report_versions WHERE report_id = $1", report_id
            )
            await conn.execute(
                "DELETE FROM public.report_generation_queue WHERE id = $1", report_id
            )


async def _current_numbers(pool: asyncpg.Pool, report_id: str) -> list[int]:
    """Version numbers flagged current — the invariant probe (read raw SQL)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT version_number FROM public.report_versions "
            "WHERE report_id = $1 AND is_current = TRUE ORDER BY version_number",
            report_id,
        )
    return [int(r["version_number"]) for r in rows]


# ---------------------------------------------------------------------------
# S1 — report version correctness (``is_current``)
# ---------------------------------------------------------------------------


async def test_iv_s1_1_demotion_and_insert_share_one_transaction(
    pool: asyncpg.Pool,
) -> None:
    """IV-S1-1 — a failed insert must roll the demotion back (spec §7.3).

    A pre-existing row occupying ``version_number = 2`` makes the ``INSERT``
    inside ``create()`` fail on the ``(report_id, version_number)`` natural key.
    If the demotion were committed *separately* from the insert, version 1 would
    stay demoted and the report would be left with **zero** current versions —
    the exact invariant break S1 exists to prevent.
    """
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        await repo.create(report.id, version_number=1, is_current=True)
        assert await _current_numbers(pool, report.id) == [1]

        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current) VALUES ($1, 2, FALSE)",
                report.id,
            )

        with pytest.raises(asyncpg.UniqueViolationError):
            await repo.create(report.id, version_number=2, is_current=True)

        # The demotion rolled back with the failed insert: v1 is still current.
        assert await _current_numbers(pool, report.id) == [1]
    finally:
        await _cleanup(pool, report.id)


async def test_iv_s1_2_duplicate_current_versions_are_unreachable(
    pool: asyncpg.Pool,
) -> None:
    """IV-S1-2 — the invariant holds for writers that bypass the repository.

    Spec §7.3 requires ``is_current`` to be a single-valued invariant, not a
    read-time mask. With the S2 index present, even a raw write that ignores the
    repository cannot reintroduce the legacy two-current-rows defect.
    """
    report = await _make_report(pool)
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current) VALUES ($1, 1, TRUE)",
                report.id,
            )
            with pytest.raises(asyncpg.UniqueViolationError):
                await conn.execute(
                    "INSERT INTO public.report_versions "
                    "(report_id, version_number, is_current) VALUES ($1, 2, TRUE)",
                    report.id,
                )
        assert await _current_numbers(pool, report.id) == [1]
        # Non-current versions remain freely insertable (only the current flag is
        # constrained), so version history is unaffected.
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current) VALUES ($1, 2, FALSE)",
                report.id,
            )
        assert await _current_numbers(pool, report.id) == [1]
    finally:
        await _cleanup(pool, report.id)



async def test_iv_s1_3_single_and_batch_read_paths_agree(
    pool: asyncpg.Pool,
) -> None:
    """IV-S1-3 — the §7.3 legacy duplicated-current scenario resolves identically.

    Before S1 the repository never demoted the previous current row, so a report
    generated twice could carry **two** ``is_current = TRUE`` rows, and
    ``get_current`` masked that by ordering on ``version_number``. The spec
    requires the single and batch read paths to agree on which version is
    current. This probe reproduces that legacy row set (the S2 index must be
    dropped for it to be representable at all — which is itself the proof that
    the defect can no longer arise) and asserts both paths return the same,
    highest-numbered version. The index is restored unconditionally.
    """
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    async with pool.acquire() as conn:
        index_def = await conn.fetchval(
            "SELECT pg_get_indexdef(c.oid) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname = $1",
            _S2_INDEX,
        )
    assert index_def, "the S2 single-current index must exist before this probe"
    try:
        async with pool.acquire() as conn:
            await conn.execute(f"DROP INDEX public.{_S2_INDEX}")
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current) "
                "VALUES ($1, 1, TRUE), ($1, 2, TRUE)",
                report.id,
            )
        single = await repo.get_current(report.id)
        batch = await repo.current_by_reports([report.id])
        assert single is not None and single["version_number"] == 2
        assert report.id in batch
        assert batch[report.id]["version_number"] == 2
        assert batch[report.id]["id"] == single["id"]
    finally:
        await _cleanup(pool, report.id)
        async with pool.acquire() as conn:
            await conn.execute(index_def)
            restored = await conn.fetchval(
                "SELECT to_regclass($1)::text", f"public.{_S2_INDEX}"
            )
        assert restored == _S2_INDEX, "the S2 index must be restored after the probe"


async def test_iv_s1_4_next_version_number_keeps_gaps_and_ignores_current(
    pool: asyncpg.Pool,
) -> None:
    """IV-S1-4 — ``next_version_number`` is ``MAX+1``, not a count.

    The spec (§14.1) makes the version number a monotonic history marker: a gap
    in the sequence (from a removed/failed later version) must not be reused,
    and a version that is not current must not shift the next number.
    """
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        assert await repo.next_version_number(report.id) == 1
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current) "
                "VALUES ($1, 1, FALSE), ($1, 3, TRUE)",
                report.id,
            )
        assert await repo.next_version_number(report.id) == 4
    finally:
        await _cleanup(pool, report.id)


async def test_iv_s1_5_current_flag_is_scoped_per_report(
    pool: asyncpg.Pool,
) -> None:
    """IV-S1-5 — the invariant is per report instance, never global.

    Promoting a version of report B must not demote report A's current version.
    """
    repo = ReportVersionsRepository(pool)
    report_a = await _make_report(pool)
    report_b = await _make_report(pool)
    try:
        await repo.create(report_a.id, version_number=1, is_current=True)
        await repo.create(report_b.id, version_number=1, is_current=True)
        await repo.create(report_a.id, version_number=2, is_current=True)

        assert await _current_numbers(pool, report_a.id) == [2]
        assert await _current_numbers(pool, report_b.id) == [1]
    finally:
        await _cleanup(pool, report_a.id, report_b.id)



# ---------------------------------------------------------------------------
# S3 — report version lifecycle state (``status``)
# ---------------------------------------------------------------------------


async def test_iv_s3_5_column_default_is_draft(pool: asyncpg.Pool) -> None:
    """IV-S3-5 — the migration's own default governs, not the Python default.

    The repository passes ``status`` explicitly, so the implementation suite
    cannot prove that ``20260913000000`` really defaults the **column** to
    ``DRAFT`` (the ratified "a completed generation yields a DRAFT version"
    rule, spec §12.3). A raw insert that names only the required columns must
    come back as ``DRAFT``.
    """
    report = await _make_report(pool)
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO public.report_versions (report_id, version_number) "
                "VALUES ($1, 1) RETURNING status, is_current",
                report.id,
            )
            meta = await conn.fetchrow(
                "SELECT column_default, is_nullable FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'report_versions' "
                "AND column_name = 'status'"
            )
        assert row["status"] == DRAFT
        assert "DRAFT" in str(meta["column_default"])
        assert meta["is_nullable"] == "NO"
    finally:
        await _cleanup(pool, report.id)


async def test_iv_s3_6_check_constraint_admits_exactly_the_ratified_six(
    pool: asyncpg.Pool,
) -> None:
    """IV-S3-6 — the stored vocabulary is closed and case-exact.

    Both the declared constraint definition *and* its runtime behaviour are
    checked, so a constraint that is merely permissive-by-omission cannot pass.
    """
    report = await _make_report(pool)
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.report_versions (report_id, version_number) "
                "VALUES ($1, 1)",
                report.id,
            )
            definition = await conn.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'report_versions_status_check'"
            )
            assert definition, "the S3 CHECK constraint must exist"
            declared = set(re.findall(r"'([^']*)'", definition))
            assert declared == set(VERSION_STATUSES)

            # Every ratified state is accepted ...
            for state in VERSION_STATUSES:
                await conn.execute(
                    "UPDATE public.report_versions SET status = $2 WHERE report_id = $1",
                    report.id,
                    state,
                )
            # ... and nothing near-miss is (assurance states must stay impossible).
            for rejected in (
                "verified",
                "Verified",
                "draft",
                "SUPERSEDED",
                "ASSURED",
                "CERTIFIED",
                "AUDITED",
                "APPROVED_ASSURED",
                "",
                " ",
            ):
                with pytest.raises(asyncpg.CheckViolationError):
                    await conn.execute(
                        "UPDATE public.report_versions SET status = $2 "
                        "WHERE report_id = $1",
                        report.id,
                        rejected,
                    )
    finally:
        await _cleanup(pool, report.id)


async def test_iv_s3_7_status_is_not_null_and_version_scoped(
    pool: asyncpg.Pool,
) -> None:
    """IV-S3-7 — no version row can exist without a lifecycle state.

    A NULL state would make the guarded transition (``WHERE status = $expected``)
    silently unmatchable and the version unreviewable forever.
    """
    repo = ReportVersionsRepository(pool)
    report = await _make_report(pool)
    try:
        await repo.create(report.id, version_number=1, is_current=True)
        async with pool.acquire() as conn:
            with pytest.raises(asyncpg.NotNullViolationError):
                await conn.execute(
                    "UPDATE public.report_versions SET status = NULL "
                    "WHERE report_id = $1",
                    report.id,
                )
            # State is version-scoped: a second version carries its own state.
            await conn.execute(
                "INSERT INTO public.report_versions "
                "(report_id, version_number, is_current, status) "
                "VALUES ($1, 2, FALSE, 'FINAL')",
                report.id,
            )
        assert (await repo.get_by_number(report.id, 1))["status"] == DRAFT
        assert (await repo.get_by_number(report.id, 2))["status"] == "FINAL"
    finally:
        await _cleanup(pool, report.id)

