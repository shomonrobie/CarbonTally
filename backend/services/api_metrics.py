"""Phase 8-X X7 — API runtime metrics service (instrumentation + flush + read).

Authority: PO decisions `X7-D1`…`X7-D7` (prompt `CT-P8X-X7-GATE-02`).

Design (the documented collection/flush architecture, `X7-D3`):

* the existing middleware layer records one observation per **instrumented**
  request (`/api/v3/**` only) into an in-process 5-minute slot;
* a flush merges the process's slots into the **single** persisted series row
  (`X7-D1`, `X7-D3`) — keyed by wall-clock slot, so flushes from any number of
  instrumented processes merge into one series instead of per-worker rows;
* a flush happens at most once every 5 minutes (`X7-D2`), triggered
  opportunistically by request activity, so recorded data is persisted within the
  cadence without a background task or any new operational parameter;
* the read model aggregates the persisted slots inside the rolling 60-minute
  window (`X7-D5`) and returns only the approved aggregate metrics.

Instrumentation is best-effort: every failure is swallowed and logged, so an
operator-visibility feature can never become an availability risk.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Optional

from core.logging import get_logger
from domain.api_metrics import (
    FLUSH_INTERVAL_SECONDS,
    INSTRUMENTED_PREFIX,
    UNMATCHED_ROUTE,
    aggregate_slots,
    empty_slot,
    record_sample,
    slot_key,
    utcnow,
)

logger = get_logger(__name__)


def route_template(request: Any) -> str:
    """The matched route **template** for a request, never the raw URL.

    Starlette sets ``scope['route']`` once routing succeeds (available after
    ``call_next``). When nothing matched (404/mount) the sentinel ``<unmatched>``
    is used: a raw path could embed identifiers, so it is never stored.
    """
    try:
        route = request.scope.get("route")
        path = getattr(route, "path", None)
        if path:
            return str(path)
    except Exception:  # noqa: BLE001 — instrumentation must never raise
        pass
    return UNMATCHED_ROUTE


class ApiMetricsService:
    """In-process slot accumulator + 5-minute flush + read model."""

    def __init__(
        self,
        repository: Any,
        *,
        clock: Any = None,
        flush_interval_seconds: int = FLUSH_INTERVAL_SECONDS,
    ) -> None:
        self._repo = repository
        self._clock = clock or utcnow
        self._flush_interval = int(flush_interval_seconds)
        self._slots: dict[str, Any] = {}
        self._last_flush: Optional[datetime] = None

    # -- instrumentation ---------------------------------------------------

    def record(
        self,
        *,
        route: str,
        method: str,
        status_code: int,
        duration_ms: float,
        now: Optional[datetime] = None,
    ) -> None:
        """Record one observation (best-effort; never raises)."""
        try:
            moment = now or self._clock()
            key = slot_key(moment)
            slot = self._slots.get(key)
            if slot is None:
                slot = empty_slot()
                self._slots[key] = slot
            record_sample(
                slot, route=route, status_code=status_code, duration_ms=duration_ms
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("X7 metric record failed: %s", type(exc).__name__)

    # -- flush -------------------------------------------------------------

    def flush_due(self, *, now: Optional[datetime] = None) -> bool:
        """`X7-D2` — at most one flush per 5-minute interval."""
        moment = now or self._clock()
        if self._last_flush is None:
            return True
        return moment - self._last_flush >= timedelta(seconds=self._flush_interval)

    async def flush(self, *, now: Optional[datetime] = None) -> dict[str, Any]:
        """Persist the buffered slots into the single series row (best-effort)."""
        moment = now or self._clock()
        buffered, self._slots = self._slots, {}
        self._last_flush = moment
        if not buffered:
            return {}
        try:
            return await self._repo.merge_slots(buffered, now=moment)
        except Exception as exc:  # noqa: BLE001 — never break a request
            logger.warning("X7 metric flush failed: %s", type(exc).__name__)
            return {}

    async def flush_if_due(self, *, now: Optional[datetime] = None) -> bool:
        if not self.flush_due(now=now):
            return False
        await self.flush(now=now)
        return True

    async def observe_request(
        self,
        request: Any,
        *,
        status_code: int,
        duration_ms: float,
        now: Optional[datetime] = None,
    ) -> None:
        """Record one HTTP request and opportunistically flush when due."""
        path = ""
        try:
            path = request.url.path or ""
        except Exception:  # noqa: BLE001
            path = ""
        if not str(path).startswith(INSTRUMENTED_PREFIX):
            return
        self.record(
            route=route_template(request),
            method=str(getattr(request, "method", "") or ""),
            status_code=status_code,
            duration_ms=duration_ms,
            now=now,
        )
        await self.flush_if_due(now=now)

    # -- read model --------------------------------------------------------

    async def read(self, *, now: Optional[datetime] = None) -> dict[str, Any]:
        """Aggregate the persisted series over the rolling 60-minute window."""
        moment = now or self._clock()
        payload = await self._repo.read_series()
        slots = (payload or {}).get("slots") or {}
        aggregate = aggregate_slots(slots, now=moment)
        aggregate["persisted_at"] = (payload or {}).get("persisted_at")
        aggregate["series_present"] = bool(payload)
        aggregate["pending_local_slots"] = len(self._slots)
        return aggregate


#: Process-wide registry used by the middleware (one merged series — `X7-D3`).
_service: Optional["ApiMetricsService"] = None


def set_service(service: Optional["ApiMetricsService"]) -> None:
    global _service
    _service = service


def get_service() -> Optional["ApiMetricsService"]:
    return _service


def monotonic_ms() -> float:
    return time.perf_counter() * 1000.0

