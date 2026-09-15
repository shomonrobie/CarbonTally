"""Phase 8-X X2 — O7: the worker tick wires heartbeat + alert evaluation.

Locks the two behaviours the worker must guarantee:

1. the X1 heartbeat is written on every tick (liveness), and
2. the X2 alert evaluation is dispatched **as a background task**, so an email
   retry storm (~15 minutes) can never stall the claim loop.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from workers.automatic_processing import AutomaticProcessingWorker

pytestmark = pytest.mark.asyncio


class _FakeProcessing:
    def __init__(self) -> None:
        self.heartbeats: list[dict[str, Any]] = []
        self.claims = 0

    async def claim_next(self, token: str, *, limit: int, stale_after_seconds: int):
        self.claims += 1
        return []

    async def record_worker_heartbeat(self, **kwargs: Any) -> dict:
        self.heartbeats.append(kwargs)
        return {"id": "hb-1"}


class _FakeRepos:
    def __init__(self) -> None:
        self.processing = _FakeProcessing()


async def test_tick_writes_heartbeat_and_schedules_alert_dispatch(monkeypatch) -> None:
    worker = AutomaticProcessingWorker(poll_interval_seconds=0.01, batch_size=1)
    repos = _FakeRepos()
    worker._repos = repos          # skip the lazy repository wiring
    worker._service = object()

    dispatched: list[dict[str, Any]] = []

    async def _fake_dispatch(self, *, now=None, actor="system"):  # noqa: ANN001
        dispatched.append({"actor": actor})
        return {"alerts": ["WORKER_STALE"], "recipients": 1, "dispatched": [{}]}

    monkeypatch.setattr(
        "services.operational_alerting.OperationalAlertingService.evaluate_and_dispatch",
        _fake_dispatch,
    )

    await worker._tick()

    # X1 — the heartbeat is always written, even on an idle tick.
    assert repos.processing.heartbeats, "the worker must tick its heartbeat"
    assert repos.processing.claims == 1

    # X2 — dispatch is scheduled in the BACKGROUND (never awaited by the loop).
    assert worker._alert_task is not None, "alert dispatch must be scheduled"
    await asyncio.wait_for(worker._alert_task, timeout=2)
    assert dispatched, "the alerting service must be invoked"
    assert dispatched[0]["actor"] == worker._worker_id


async def test_tick_survives_an_alerting_failure(monkeypatch) -> None:
    """Alerting must never break processing: a failing dispatch is contained."""
    worker = AutomaticProcessingWorker(poll_interval_seconds=0.01, batch_size=1)
    repos = _FakeRepos()
    worker._repos = repos
    worker._service = object()

    async def _boom(self, *, now=None, actor="system"):  # noqa: ANN001
        raise RuntimeError("alerting exploded")

    monkeypatch.setattr(
        "services.operational_alerting.OperationalAlertingService.evaluate_and_dispatch",
        _boom,
    )

    await worker._tick()  # must not raise

    assert worker._alert_task is not None
    with pytest.raises(RuntimeError):
        await worker._alert_task
    assert repos.processing.heartbeats, "heartbeat still written after a failed dispatch"
