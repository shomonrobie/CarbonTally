"""Unit tests for the PD-2 scheduled-report runner (CT-IMPLEMENT-02).

The runner is exercised against an in-memory store that reproduces the two
behaviours the canonical schema is responsible for: the UNIQUE
``(schedule_id, scheduled_for)`` refusal (idempotency) and terminal run states
that a run may enter only once. No database is required and no report is
fabricated.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any, Mapping, Optional

import pytest

from domain.report_schedule import ProducedReport, ScheduleConfigurationError, ScheduleDefinition
from services.report_schedule_runner import (
    AUDIT_RUN_FAILED,
    AUDIT_RUN_SKIPPED,
    AUDIT_RUN_SUCCEEDED,
    AUDIT_SLOT_DEDUPLICATED,
    DUPLICATE_SLOT,
    ERROR_INVALID_CONFIGURATION,
    ERROR_NO_REPORT,
    ReportScheduleRunner,
)

NOW = datetime(2026, 2, 1, 7, 30, tzinfo=timezone.utc)
SLOT = datetime(2026, 2, 1, 7, 0, tzinfo=timezone.utc)


def schedule_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": "schedule-1",
        "organization_id": "org-1",
        "name": "Monthly pack",
        "report_type": "annual",
        "reporting_year": 2026,
        "frequency": "monthly",
        "run_time": time(7, 0),
        "timezone": "Europe/London",
        "next_run_at": SLOT,
        "failure_count": 0,
        "recipients": [{"email": "owner@example.com"}],
    }
    row.update(overrides)
    return row


class FakeStore:
    """In-memory stand-in for the canonical schedule tables."""

    def __init__(self, rows: list[Mapping[str, Any]]) -> None:
        self.rows = list(rows)
        self.claimed: set[tuple[str, datetime]] = set()
        self.runs: list[dict[str, Any]] = []
        self.outcomes: list[dict[str, Any]] = []
        self.due_calls: list[tuple[datetime, int]] = []

    async def due_schedules(self, now: datetime, limit: int) -> list[Mapping[str, Any]]:
        self.due_calls.append((now, limit))
        return [r for r in self.rows if (r.get("next_run_at") or now) <= now][:limit]

    async def open_run(
        self, schedule: ScheduleDefinition, *, scheduled_for: datetime, attempt: int
    ) -> Optional[str]:
        key = (schedule.id, scheduled_for)
        if key in self.claimed:
            return None  # UNIQUE (schedule_id, scheduled_for) refusal
        self.claimed.add(key)
        run_id = f"run-{len(self.claimed)}"
        self.runs.append(
            {
                "id": run_id,
                "schedule_id": schedule.id,
                "scheduled_for": scheduled_for,
                "attempt": attempt,
                "status": "running",
            }
        )
        return run_id

    async def finish_run(self, run_id: str, **fields: Any) -> None:
        run = next(r for r in self.runs if r["id"] == run_id)
        assert run["status"] == "running", "a run may only transition once"
        run.update(fields)

    async def record_outcome(self, schedule: ScheduleDefinition, **fields: Any) -> None:
        self.outcomes.append(dict(fields, schedule_id=schedule.id))


class Recorder:
    """Captures audit appends; optionally fails like an unavailable sink."""

    def __init__(self, fail: bool = False) -> None:
        self.entries: list[tuple[str, Mapping[str, Any]]] = []
        self.fail = fail

    async def __call__(self, action: str, payload: Mapping[str, Any]) -> None:
        if self.fail:
            raise RuntimeError("audit backend unavailable")
        self.entries.append((action, payload))

    def actions(self) -> list[str]:
        return [action for action, _ in self.entries]


def make_runner(store: FakeStore, producer: Any, audit: Optional[Recorder] = None):
    async def produce(schedule: ScheduleDefinition, *, scheduled_for: datetime) -> Any:
        return await producer(schedule, scheduled_for)

    return ReportScheduleRunner(store, produce=produce, audit_sink=audit, clock=lambda: NOW)



async def test_successful_run_records_the_canonical_artefacts() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder()
    produced: list[datetime] = []

    async def producer(schedule, scheduled_for):
        produced.append(scheduled_for)
        return ProducedReport(report_id="rep-1", report_version_id="ver-1",
                              result_summary={"rows": 12})

    tick = await make_runner(store, producer, audit).run_due()

    assert produced == [SLOT]
    assert (tick.due, tick.succeeded, tick.failed) == (1, 1, 0)
    assert store.runs[0]["status"] == "succeeded"
    assert store.runs[0]["report_id"] == "rep-1"
    assert store.runs[0]["report_version_id"] == "ver-1"
    outcome = store.outcomes[0]
    assert outcome["last_result"] == "succeeded"
    assert outcome["failure_count"] == 0
    assert outcome["is_active"] is True
    assert outcome["next_run_at"] == datetime(2026, 3, 1, 7, 0, tzinfo=timezone.utc)
    assert audit.actions() == [AUDIT_RUN_SUCCEEDED]
    assert audit.entries[0][1]["correlation_id"] == "schedule-1"


async def test_repeated_tick_for_the_same_slot_is_idempotent() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder()
    calls: list[datetime] = []

    async def producer(schedule, scheduled_for):
        calls.append(scheduled_for)
        return ProducedReport(report_id="rep-1")

    runner = make_runner(store, producer, audit)
    await runner.run_due()
    # The schedule still carries the same persisted due time, as it would if the
    # state write had not yet landed: the second tick must not run again.
    second = await runner.run_due()

    assert calls == [SLOT]
    assert len(store.runs) == 1
    assert (second.duplicate_slots, second.executed) == (1, 0)
    assert second.outcomes[0].detail == DUPLICATE_SLOT
    assert audit.actions() == [AUDIT_RUN_SUCCEEDED, AUDIT_SLOT_DEDUPLICATED]


async def test_producer_returning_nothing_records_a_described_skip() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder()

    async def producer(schedule, scheduled_for):
        return None

    tick = await make_runner(store, producer, audit).run_due()

    assert (tick.skipped, tick.succeeded, tick.failed) == (1, 0, 0)
    assert store.runs[0]["status"] == "skipped"
    assert store.outcomes[0]["last_result"] == "skipped"
    assert store.outcomes[0]["failure_count"] == 0  # a skip is not a failure
    assert store.outcomes[0]["next_run_at"] == datetime(2026, 3, 1, 7, 0, tzinfo=timezone.utc)
    assert audit.actions() == [AUDIT_RUN_SKIPPED]


async def test_producer_failure_retries_with_backoff() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder()

    class Boom(RuntimeError):
        code = "engine_unavailable"

    async def producer(schedule, scheduled_for):
        raise Boom("engine offline")

    tick = await make_runner(store, producer, audit).run_due()

    assert (tick.failed, tick.paused) == (1, 0)
    run = store.runs[0]
    assert run["status"] == "failed"
    assert run["error_code"] == "engine_unavailable"
    assert run["error_message"] == "engine offline"
    outcome = store.outcomes[0]
    assert outcome["last_result"] == "failed"
    assert outcome["failure_count"] == 1
    assert outcome["is_active"] is True
    # Backoff after the first failure is the policy's first interval (5 minutes).


async def test_retries_exhausted_pauses_the_schedule() -> None:
    store = FakeStore([schedule_row(failure_count=2)])  # the default allows 3 attempts
    audit = Recorder()

    async def producer(schedule, scheduled_for):
        raise RuntimeError("still failing")

    tick = await make_runner(store, producer, audit).run_due()

    assert (tick.failed, tick.paused) == (1, 1)
    outcome = store.outcomes[0]
    assert outcome["failure_count"] == 3
    assert outcome["is_active"] is False
    assert outcome["paused_at"] == NOW  # the schema requires a pause timestamp
    assert outcome["last_error"] == "still failing"
    assert tick.outcomes[0].paused is True


async def test_success_without_a_report_id_is_a_failure() -> None:
    store = FakeStore([schedule_row()])

    async def producer(schedule, scheduled_for):
        return ProducedReport(report_id="")

    tick = await make_runner(store, producer).run_due()

    assert (tick.failed, tick.succeeded) == (1, 0)
    assert store.runs[0]["error_code"] == ERROR_NO_REPORT
    assert store.outcomes[0]["last_result"] == "failed"


async def test_unusable_stored_configuration_fails_and_pauses() -> None:
    store = FakeStore([schedule_row(frequency="daily")])  # the legacy advertisement

    async def producer(schedule, scheduled_for):  # must never run
        raise AssertionError("the producer must not run for an invalid schedule")

    tick = await make_runner(store, producer).run_due()

    assert (tick.failed, tick.paused) == (1, 1)
    assert store.runs[0]["error_code"] == ERROR_INVALID_CONFIGURATION
    assert store.outcomes[0]["is_active"] is False


async def test_audit_failure_does_not_break_execution() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder(fail=True)

    async def producer(schedule, scheduled_for):
        return ProducedReport(report_id="rep-1")

    tick = await make_runner(store, producer, audit).run_due()

    assert tick.succeeded == 1
    assert store.runs[0]["status"] == "succeeded"
    assert audit.entries == []


async def test_not_due_schedules_are_left_alone() -> None:
    store = FakeStore(
        [schedule_row(next_run_at=datetime(2026, 3, 1, 7, 0, tzinfo=timezone.utc))]
    )

    async def producer(schedule, scheduled_for):
        raise AssertionError("nothing is due")

    tick = await make_runner(store, producer).run_due()

    assert tick.due == 0 and tick.outcomes == ()
    assert store.runs == [] and store.outcomes == []


async def test_due_selection_uses_the_persisted_due_time_and_limit() -> None:
    store = FakeStore([schedule_row()])
    audit = Recorder()

    async def producer(schedule, scheduled_for):
        return ProducedReport(report_id="rep-1")

    await make_runner(store, producer, audit).run_due()

    assert store.due_calls == [(NOW, 25)]
    assert audit.entries[0][1]["actor_type"] == "system"


async def test_runner_rejects_a_naive_tick_time() -> None:
    store = FakeStore([])

    async def producer(schedule, scheduled_for):
        return None

    runner = make_runner(store, producer)
    with pytest.raises(ScheduleConfigurationError):
        await runner.run_due(now=datetime(2026, 2, 1, 7, 30))
