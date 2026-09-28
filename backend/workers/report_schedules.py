"""Canonical scheduled-report worker (CT-IMPLEMENT-03 / PD-2).

The durable, server-side trigger PD-2 requires: a lifespan-managed asyncio loop
that periodically executes due report schedules through
``services.report_schedule_runner``. Without it, schedules are only *definitions*
— this is what makes a scheduled report actually get produced.

Design (mirrors ``workers.automatic_processing``):

* ``tick()`` resolves the process repository bundle, builds the canonical runner
  and calls ``run_due()``;
* due selection is persisted (``report_schedule_definitions.next_run_at``) and the
  per-slot UNIQUE constraint makes execution idempotent, so two workers, a restart
  or a slow tick can never produce a duplicate report;
* a failed tick is logged and never kills the loop;
* ``stop()`` cancels the loop; ``run_once()`` exists so operations (and the
  integration suite) can execute exactly one tick deterministically.

Environment toggle: ``CT_REPORT_SCHEDULES_ENABLED`` (default ``1``). Setting it
to ``0`` disables the loop without removing the surface — useful when schedules
are executed by an external scheduler that calls ``run_once()``.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Optional

from core.logging import get_logger
from services.report_schedule_producer import CanonicalReportProducer
from services.report_schedule_runner import (
    DEFAULT_DUE_LIMIT,
    ReportScheduleRunner,
    TickReport,
)
from services.report_schedules import build_audit_sink

logger = get_logger(__name__)

#: Default poll interval (one tick per minute): schedules are configured to a
#: local time-of-day, so minute granularity is the finest resolution that means
#: anything, and a slower tick keeps idle load negligible.
DEFAULT_POLL_INTERVAL_SECONDS = 60.0


def _enabled() -> bool:
    """Whether the background loop should run (``CT_REPORT_SCHEDULES_ENABLED``)."""
    return os.getenv("CT_REPORT_SCHEDULES_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


class ReportScheduleWorker:
    """Background due-schedule loop backed by the canonical runner."""

    def __init__(
        self,
        *,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        due_limit: int = DEFAULT_DUE_LIMIT,
    ) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._due_limit = due_limit
        self._task: Optional[asyncio.Task] = None
        self._stopping = False
        self._runner: Optional[ReportScheduleRunner] = None

    # -- lifecycle ----------------------------------------------------------
    async def start(self) -> None:
        """Begin the background tick loop (idempotent)."""
        if not _enabled():
            logger.info(
                "report-schedule worker disabled (CT_REPORT_SCHEDULES_ENABLED=0)"
            )
            return
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        self._task = asyncio.create_task(self._run_loop(), name="report-schedule-worker")
        logger.info(
            "report-schedule worker started (poll %.1fs, due limit %d)",
            self._poll_interval_seconds,
            self._due_limit,
        )

    async def stop(self) -> None:
        """Stop the loop and wait for the current tick to finish."""
        self._stopping = True
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("report-schedule worker stopped")

    # -- ticking ------------------------------------------------------------
    async def _run_loop(self) -> None:
        while not self._stopping:
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — the loop must never die
                logger.exception("report-schedule tick failed: %r", exc)
            await asyncio.sleep(self._poll_interval_seconds)

    async def tick(self) -> TickReport:
        """Execute one due-schedule tick and report what actually happened."""
        runner = await self._get_runner()
        report = await runner.run_due()
        if report.due or report.executed:
            logger.info(
                "report schedules: due=%d executed=%d succeeded=%d skipped=%d "
                "failed=%d paused=%d duplicate_slots=%d",
                report.due,
                report.executed,
                report.succeeded,
                report.skipped,
                report.failed,
                report.paused,
                report.duplicate_slots,
            )
        return report

    async def run_once(self, *, now: Optional[datetime] = None) -> TickReport:
        """Execute exactly one tick (operations / integration verification)."""
        runner = await self._get_runner()
        return await runner.run_due(now=now)

    async def _get_runner(self) -> ReportScheduleRunner:
        """Build the canonical runner once per worker process."""
        if self._runner is not None:
            return self._runner
        from api.dependencies import (
            build_report_engine,
            get_audit_logger,
            get_event_bus,
            get_repositories,
        )

        repos = await get_repositories()
        engine = build_report_engine(
            repos,
            event_bus=await get_event_bus(),
            audit_logger=await get_audit_logger(),
        )
        self._runner = ReportScheduleRunner(
            repos.report_schedules,
            produce=CanonicalReportProducer(repos, engine),
            audit_sink=build_audit_sink(repos),
            due_limit=self._due_limit,
        )
        return self._runner


#: Process-wide worker singleton (started/stopped by the FastAPI lifespan).
_worker: Optional[ReportScheduleWorker] = None


def get_report_schedule_worker() -> ReportScheduleWorker:
    """Return the process-wide report-schedule worker singleton."""
    global _worker
    if _worker is None:
        _worker = ReportScheduleWorker()
    return _worker
