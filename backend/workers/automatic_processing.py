"""Durable automatic-processing background worker (V3 Phase A / CL-56).

A lifespan-managed asyncio loop that claims runnable jobs from
``document_processing_queue`` (``FOR UPDATE SKIP LOCKED``) and runs each job
through :class:`services.automatic_processing.AutomaticProcessingService`.
Job state lives in the database, so a worker restart resumes every in-flight
job (stale claims are recovered and stage outputs are the idempotency markers).

Design
------
* ``tick()`` runs on a poll interval; each tick claims up to ``batch_size``
  jobs and processes them concurrently.
* A failed tick never stops the loop — it is logged and the loop continues.
* ``stop()`` cancels the loop task; ``_stopping`` guarantees no new claim once
  shutdown has begun.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from core.logging import get_logger
from engines.calculation import DEFAULT_ALGORITHM_VERSION, CalculationEngine
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.matching_stages import RepositoryAliasResolver
from infra.audit_logger import AuditLogger
from infra.event_bus import get_event_bus
from infra.search_index import FactorSearchIndex

logger = get_logger(__name__)


class AutomaticProcessingWorker:
    """Background claim/process loop for the durable pipeline."""

    def __init__(
        self,
        *,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 3,
        stale_lock_seconds: int = 300,
    ) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._stale_lock_seconds = stale_lock_seconds
        self._task: Optional[asyncio.Task] = None
        self._stopping = False
        self._repos = None
        self._service = None

    # -- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        """Begin the background claim loop (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        self._task = asyncio.create_task(
            self._run_loop(), name="automatic-processing-worker"
        )
        logger.info(
            "automatic-processing worker started (poll %.1fs, batch %d)",
            self._poll_interval_seconds,
            self._batch_size,
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
        logger.info("automatic-processing worker stopped")

    # -- loop ---------------------------------------------------------------

    async def _run_loop(self) -> None:
        while not self._stopping:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — the loop must never die
                logger.exception("automatic-processing tick failed: %r", exc)
            await asyncio.sleep(self._poll_interval_seconds)

    async def _tick(self) -> None:
        if self._repos is None:
            from api.dependencies import get_repositories

            self._repos = await get_repositories()
            self._service = await self._build_service(self._repos)
        token = f"worker::{uuid.uuid4().hex}"
        jobs = await self._repos.processing.claim_next(
            token,
            limit=self._batch_size,
            stale_after_seconds=self._stale_lock_seconds,
        )
        if not jobs:
            return
        results = await asyncio.gather(
            *(self._process_one(job, token) for job in jobs),
            return_exceptions=True,
        )
        for job, outcome in zip(jobs, results):
            if isinstance(outcome, BaseException):
                logger.exception("job %s crashed during processing", job.id)
                try:
                    await self._repos.processing.mark_failed(
                        job.id,
                        last_error=f"worker exception: {outcome}"[:1000],
                        lock_token=token,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("failed to dead-letter job %s", job.id)

    async def _process_one(self, job, token: str) -> None:
        await self._service.process_job(job, token)

    # -- wiring -------------------------------------------------------------

    async def _build_service(self, repos):
        from services.automatic_processing import AutomaticProcessingService

        event_bus = get_event_bus()
        audit_logger = AuditLogger(repos.audit)

        index = FactorSearchIndex()
        factors = await repos.factors.load_all_for_index()
        index.load(factors)
        from domain.matching import MatchingPipelineConfig

        config = MatchingPipelineConfig()
        stages = build_matching_pipeline(
            config, alias_resolver=RepositoryAliasResolver(repos.aliases)
        )
        matching_engine = FactorMatchingEngine(
            index,
            stages,
            config=config,
            event_bus=event_bus,
            audit_logger=audit_logger,
            customer_factor_lookup=repos.customer_factors,
        )
        calculation_engine = CalculationEngine(
            sink=repos.logs,
            event_bus=event_bus,
            audit_logger=audit_logger,
            algorithm_version=DEFAULT_ALGORITHM_VERSION,
        )
        return AutomaticProcessingService(
            repos,
            event_bus=event_bus,
            audit_logger=audit_logger,
            matching_engine=matching_engine,
            calculation_engine=calculation_engine,
        )


#: Process-wide worker singleton (started/stopped by the FastAPI lifespan).
_worker: Optional[AutomaticProcessingWorker] = None


def get_automatic_processing_worker() -> AutomaticProcessingWorker:
    """Return the process-wide worker singleton."""
    global _worker
    if _worker is None:
        _worker = AutomaticProcessingWorker()
    return _worker

