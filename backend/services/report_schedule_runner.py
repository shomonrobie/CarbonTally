"""CT-IMPLEMENT-02 (PD-2) — canonical scheduled-report execution runner.

Ratified PO decision **PD-2**: scheduled reporting must actually execute. The
schema half is
``supabase/migrations/20261023000000_ct02_scheduled_reporting.sql``; the pure
half is :mod:`domain.report_schedule`. This module is the orchestration half it
names explicitly ("orchestration is the application's job — see
backend/services/report_schedule_runner.py").

What it guarantees, against the canonical tables only
(``report_schedule_definitions`` + ``report_schedule_runs`` — never the retired
``report_schedules``):

* **Due selection is persisted, not remembered.** Due schedules are read from
  ``next_run_at`` by the store for each tick, so a restart resumes from the
  database.
* **One row per due slot.** ``open_run`` inserts ``(schedule_id,
  scheduled_for)``; the table's UNIQUE constraint makes a repeated tick a no-op,
  so a schedule can never produce a duplicate report.
* **Real outcomes only.** A run records ``succeeded`` with the canonical
  report/version it produced, ``skipped`` with the reason it produced nothing, or
  ``failed`` with an error code and message. A producer that returns success
  without naming a report is a failure, never a success.
* **Bounded retry.** Failures increment ``failure_count`` and schedule the next
  attempt using ``retry_policy`` backoff; when ``max_attempts`` is exhausted the
  schedule is paused (``is_active = false`` + ``paused_at``) rather than retried
  forever.
* **Audited.** Every outcome appends a canonical audit entry with
  ``correlation_id = schedule id``, as the migration's table comment requires.
  An audit failure is logged and never breaks execution.

The store, the producer and the audit sink are injected: this service holds no
database client, so it is unit-testable without a database and cannot itself
bypass RLS or the report workflow.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Mapping, Optional, Protocol, Sequence

from core.logging import get_logger
from domain.report_schedule import (
    FAILED,
    RUNNING,
    SKIPPED,
    SUCCEEDED,
    ProducedReport,
    ScheduleConfigurationError,
    ScheduleDefinition,
    attempt_number,
    backoff_delta,
    can_retry,
    is_due,
    next_occurrence,
)

logger = get_logger(__name__)

#: Audit actions appended to ``public.audit_trail`` (correlation_id = schedule id).
AUDIT_RUN_SUCCEEDED = "report_schedule_run_succeeded"
AUDIT_RUN_FAILED = "report_schedule_run_failed"
AUDIT_RUN_SKIPPED = "report_schedule_run_skipped"
AUDIT_SLOT_DEDUPLICATED = "report_schedule_run_slot_deduplicated"

#: How many due schedules one tick processes (bounded work per tick).
DEFAULT_DUE_LIMIT = 25

#: Detail recorded on a run outcome whose due slot was already executed.
DUPLICATE_SLOT = "duplicate_slot"

#: Stable error code for a producer that produced nothing reportable.
ERROR_NO_REPORT = "no_report_produced"
#: Stable error code for a stored configuration the canonical model rejects.
ERROR_INVALID_CONFIGURATION = "invalid_schedule_configuration"


class ScheduleStore(Protocol):
    """The canonical persistence contract for the runner.

    Implemented by the data layer against ``report_schedule_definitions`` and
    ``report_schedule_runs``; kept as a protocol so the orchestration can be
    verified without a database.
    """

    async def due_schedules(self, now: datetime, limit: int) -> Sequence[Mapping[str, Any]]:
        """Schedules whose persisted ``next_run_at`` has arrived."""

    async def open_run(
        self, schedule: ScheduleDefinition, *, scheduled_for: datetime, attempt: int
    ) -> Optional[str]:
        """Claim the due slot, returning the run id.

        Returns ``None`` when the slot already has a run row (the UNIQUE
        ``(schedule_id, scheduled_for)`` refusal) — the idempotent case.
        """

    async def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        report_id: Optional[str] = None,
        report_version_id: Optional[str] = None,
        result_summary: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Move a ``running`` run to its terminal state, exactly once."""

    async def record_outcome(
        self,
        schedule: ScheduleDefinition,
        *,
        next_run_at: datetime,
        last_result: str,
        failure_count: int,
        is_active: bool,
        last_error: Optional[str] = None,
        paused_at: Optional[datetime] = None,
    ) -> None:
        """Persist the schedule's own execution/retry state."""


class ReportProducer(Protocol):
    """Produces the canonical report for one due slot."""

    async def __call__(
        self, schedule: ScheduleDefinition, *, scheduled_for: datetime
    ) -> Optional[ProducedReport]:
        """Return the produced report/version, or ``None`` to record a skip."""


AuditSink = Callable[[str, Mapping[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class RunOutcome:
    """One schedule's outcome in a tick — observability, never a spinner."""

    schedule_id: str
    scheduled_for: Optional[datetime]
    status: str
    attempt: int
    detail: str = ""
    report_id: Optional[str] = None
    report_version_id: Optional[str] = None
    next_run_at: Optional[datetime] = None
    paused: bool = False


@dataclass(frozen=True)
class TickReport:
    """The result of one tick (what was due, what actually happened)."""

    started_at: datetime
    finished_at: datetime
    due: int = 0
    executed: int = 0
    duplicate_slots: int = 0
    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    paused: int = 0
    outcomes: tuple[RunOutcome, ...] = field(default_factory=tuple)


class ReportScheduleRunner:
    """Executes due report schedules against the canonical tables."""

    def __init__(
        self,
        store: ScheduleStore,
        *,
        produce: ReportProducer,
        audit_sink: Optional[AuditSink] = None,
        clock: Optional[Callable[[], datetime]] = None,
        due_limit: int = DEFAULT_DUE_LIMIT,
    ) -> None:
        self._store = store
        self._produce = produce
        self._audit_sink = audit_sink
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._due_limit = due_limit

    async def run_due(self, *, now: Optional[datetime] = None) -> TickReport:
        """Process every schedule whose persisted due time has arrived.

        Safe to call repeatedly and concurrently: the per-slot UNIQUE constraint
        makes a second tick for the same slot a recorded no-op.
        """
        started = now or self._clock()
        if started.tzinfo is None:
            raise ScheduleConfigurationError("the runner requires an aware tick time")

        rows = await self._store.due_schedules(started, self._due_limit)
        outcomes: list[RunOutcome] = []
        for row in rows:
            schedule = ScheduleDefinition.from_row(row)
            if not is_due(schedule.next_run_at, started):
                # The store over-selected (a race with another tick, or a paused
                # schedule); the persisted due time always wins.
                continue
            outcomes.append(await self._run_one(schedule, now=started))

        duplicated = sum(1 for o in outcomes if o.detail == DUPLICATE_SLOT)
        return TickReport(
            started_at=started,
            finished_at=self._clock(),
            due=len(rows),
            executed=len(outcomes) - duplicated,
            duplicate_slots=duplicated,
            succeeded=sum(1 for o in outcomes if o.status == SUCCEEDED),
            skipped=sum(1 for o in outcomes if o.status == SKIPPED and o.detail != DUPLICATE_SLOT),
            failed=sum(1 for o in outcomes if o.status == FAILED),
            paused=sum(1 for o in outcomes if o.paused),
            outcomes=tuple(outcomes),
        )


    # -- internal -----------------------------------------------------------
    async def _run_one(self, schedule: ScheduleDefinition, *, now: datetime) -> RunOutcome:
        scheduled_for = schedule.next_run_at
        assert scheduled_for is not None  # guaranteed by is_due
        attempt = attempt_number(schedule.failure_count)

        try:
            run_id = await self._store.open_run(
                schedule, scheduled_for=scheduled_for, attempt=attempt
            )
        except Exception:  # a failed claim must not stop the rest of the tick
            logger.exception("report schedule %s: could not claim due slot", schedule.id)
            return RunOutcome(
                schedule_id=schedule.id,
                scheduled_for=scheduled_for,
                status=FAILED,
                attempt=attempt,
                detail="claim_failed",
            )

        if run_id is None:
            # The slot is already recorded: idempotent no-op, no second report.
            await self._audit(
                AUDIT_SLOT_DEDUPLICATED,
                schedule,
                scheduled_for=scheduled_for,
                attempt=attempt,
                detail="due slot already executed",
            )
            return RunOutcome(
                schedule_id=schedule.id,
                scheduled_for=scheduled_for,
                status=SKIPPED,
                attempt=attempt,
                detail=DUPLICATE_SLOT,
            )

        try:
            next_due = self._advance(schedule, scheduled_for)
        except ScheduleConfigurationError as exc:
            # A stored configuration the canonical model rejects. The run is
            # recorded as a failure with a code, and the schedule is paused rather
            # than retried: retrying cannot repair it.
            return await self._finish(
                schedule,
                run_id=run_id,
                scheduled_for=scheduled_for,
                status=FAILED,
                attempt=attempt,
                error_code=ERROR_INVALID_CONFIGURATION,
                error_message=str(exc)[:500],
                next_due=now,
                now=now,
                pause=True,
            )

        try:
            produced = await self._produce(schedule, scheduled_for=scheduled_for)
        except Exception as exc:  # noqa: BLE001 — recorded as a real failure
            return await self._fail(
                schedule,
                run_id=run_id,
                scheduled_for=scheduled_for,
                attempt=attempt,
                error_code=_error_code(exc),
                error_message=str(exc)[:500] or "report production failed",
                next_due=next_due,
                now=now,
            )

        if produced is None:
            return await self._finish(
                schedule,
                run_id=run_id,
                scheduled_for=scheduled_for,
                status=SKIPPED,
                attempt=attempt,
                detail="producer reported nothing to deliver",
                next_due=next_due,
                now=now,
            )

        report_id = getattr(produced, "report_id", None)
        if not report_id:
            # "Success" without a canonical report is not a success.
            return await self._fail(
                schedule,
                run_id=run_id,
                scheduled_for=scheduled_for,
                attempt=attempt,
                error_code=ERROR_NO_REPORT,
                error_message="the producer returned no canonical report id",
                next_due=next_due,
                now=now,
            )

        return await self._finish(
            schedule,
            run_id=run_id,
            scheduled_for=scheduled_for,
            status=SUCCEEDED,
            attempt=attempt,
            report_id=str(report_id),
            report_version_id=getattr(produced, "report_version_id", None),
            result_summary=getattr(produced, "result_summary", None),
            next_due=next_due,
            now=now,
        )

    # -- internal -----------------------------------------------------------
    def _advance(self, schedule: ScheduleDefinition, scheduled_for: datetime) -> datetime:
        """The next due time after this slot, in the schedule's own timezone."""
        return next_occurrence(
            schedule.frequency,
            schedule.run_time,
            schedule.timezone,
            scheduled_for,
            from_date=scheduled_for.date(),
        )

    async def _fail(
        self,
        schedule: ScheduleDefinition,
        *,
        run_id: str,
        scheduled_for: datetime,
        attempt: int,
        error_code: str,
        error_message: str,
        next_due: datetime,
        now: datetime,
    ) -> RunOutcome:
        """Record a failure, apply the retry policy, and pause when exhausted."""
        failure_count = schedule.failure_count + 1
        retryable = can_retry(schedule.retry_policy, failure_count)
        return await self._finish(
            schedule,
            run_id=run_id,
            scheduled_for=scheduled_for,
            status=FAILED,
            attempt=attempt,
            error_code=error_code,
            error_message=error_message,
            next_due=now + backoff_delta(schedule.retry_policy, failure_count) if retryable else next_due,
            now=now,
            failure_count=failure_count,
            pause=not retryable,
        )

    async def _finish(
        self,
        schedule: ScheduleDefinition,
        *,
        run_id: str,
        scheduled_for: datetime,
        status: str,
        attempt: int,
        next_due: datetime,
        now: datetime,
        detail: str = "",
        report_id: Optional[str] = None,
        report_version_id: Optional[str] = None,
        result_summary: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        failure_count: Optional[int] = None,
        pause: bool = False,
    ) -> RunOutcome:
        """Close the run, persist the schedule state and audit the outcome."""
        failure_count = schedule.failure_count if failure_count is None else failure_count
        await self._store.finish_run(
            run_id,
            status=status,
            report_id=report_id,
            report_version_id=report_version_id,
            result_summary=dict(result_summary) if result_summary else None,
            error_code=error_code,
            error_message=error_message,
        )
        await self._store.record_outcome(
            schedule,
            next_run_at=next_due,
            last_result=status,
            failure_count=failure_count,
            is_active=not pause,
            last_error=error_message,
            paused_at=now if pause else None,
        )
        await self._audit(
            {
                SUCCEEDED: AUDIT_RUN_SUCCEEDED,
                FAILED: AUDIT_RUN_FAILED,
                SKIPPED: AUDIT_RUN_SKIPPED,
            }.get(status, AUDIT_RUN_SKIPPED),
            schedule,
            scheduled_for=scheduled_for,
            attempt=attempt,
            run_id=run_id,
            status=status,
            detail=detail or error_message or "",
            report_id=report_id,
            report_version_id=report_version_id,
            next_run_at=next_due,
        )
        if pause:
            logger.warning(
                "report schedule %s paused after %s failed attempt(s): %s",
                schedule.id,
                failure_count,
                error_message or detail,
            )
        return RunOutcome(
            schedule_id=schedule.id,
            scheduled_for=scheduled_for,
            status=status,
            attempt=attempt,
            detail=detail or error_message or "",
            report_id=report_id,
            report_version_id=report_version_id,
            next_run_at=next_due,
            paused=pause,
        )

    async def _audit(self, action: str, schedule: ScheduleDefinition, **fields: Any) -> None:
        """Append one canonical audit entry (best-effort by design).

        ``correlation_id`` is the schedule id, as the migration's table comment
        requires. An audit failure is logged, never allowed to break a run or to
        turn a real outcome into a fake one.
        """
        if self._audit_sink is None:
            return
        payload: dict[str, Any] = {
            "correlation_id": schedule.id,
            "organization_id": schedule.organization_id,
            "actor": "system",
            "actor_type": "system",
            "report_schedule_id": schedule.id,
        }
        payload.update({k: v for k, v in fields.items() if v is not None})
        try:
            await self._audit_sink(action, payload)
        except Exception:  # noqa: BLE001 — audit must never break execution
            logger.exception(
                "report schedule %s: audit append failed for %s", schedule.id, action
            )


def _error_code(exc: BaseException) -> str:
    """A stable, non-empty error code for a recorded failure."""
    code = getattr(exc, "code", None) or getattr(exc, "error_code", None)
    if isinstance(code, str) and code.strip():
        return code.strip()[:64]
    return type(exc).__name__[:64] or "unknown_error"

