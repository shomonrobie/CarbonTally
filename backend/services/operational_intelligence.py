"""Phase 8-X X4 — operational intelligence aggregation (read-only; failures + SLA).

Authority: PO decision of 2026-09-14 approving the bounded contract
``CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md`` with rulings

* **`X4-D1` window-less** first release — no trend/time-window semantics at all;
* **`X4-D2`** an explicit ``truncated`` flag whenever the existing 2,000-row queue
  read bound can make an aggregate incomplete;
* **`X4-D3`** no failure-rate metric — no denominator is invented;
* **`X4-D4` flag-only SLA** — the persisted ``sla_breached`` signal only; the separate
  deadline-derived semantic in ``data/reporting.py`` is deliberately untouched;
* **`X4-D5`** one read-only operator aggregation endpoint.

Hard boundaries: no new processing/calculation engine, no new table/view/column/
migration, no RLS change, no new permission model, no per-organisation breakdown, and
no document contents, filenames, signed URLs or raw ``last_error`` values in any
response. X1 semantics and X2 alerting are reused **unchanged**, never re-run here.

This module is a pure composition layer: every number it reports is produced by the
existing X1 predicates in :mod:`domain.operational_health` or read from an existing
persisted column/setting, so X4 and X1 can never disagree about the same row.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from core.logging import get_logger
from domain.operational_health import (
    CLOSED_STAGES,
    DEFAULT_STALE_AFTER_SECONDS,
    HEARTBEAT_UNKNOWN,
    OPEN_STAGES,
    classify_worker_liveness,
    is_retry_exhausted,
    is_stuck,
    stage_distribution,
)

logger = get_logger(__name__)

#: The existing X1 read bound. Named here so the response can be honest about it
#: (X4-D2) instead of presenting a partial population as the whole.
QUEUE_READ_LIMIT = 2000

#: Persisted queue vocabulary used by the approved metrics (X1 stages).
FAILED_STAGE = "failed"
BLOCKED_STAGE = "blocked"
MANUAL_REVIEW_STAGE = "manual_review"
UNKNOWN_STAGE = "UNKNOWN"

#: ``sla_state`` vocabulary (contract M8).
SLA_STATE_CONFIGURED = "configured"
SLA_STATE_NOT_CONFIGURED = "not_configured"
SLA_STATE_UNKNOWN = "unknown"

#: The endpoint's declared scope marker (mirrors X1's ``x1_scope`` convention).
X4_SCOPE = "failures_and_sla"


# ---------------------------------------------------------------------------
# Pure aggregation (no I/O) — unit-testable per metric
# ---------------------------------------------------------------------------


def aggregate_queue_rows(
    rows: Iterable[dict[str, Any]],
    *,
    limit: int = QUEUE_READ_LIMIT,
    now: Optional[datetime] = None,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Compose the approved failure/queue metrics from persisted queue rows.

    Every count comes from an existing X1 predicate or an existing persisted
    column. ``truncated`` is true when the read returned exactly the bound, i.e.
    when further rows may exist and the aggregates are therefore a floor, not a
    total (X4-D2) — never silently reported as a complete population.
    """
    now = now or datetime.now(timezone.utc)
    materialised = list(rows)

    errors_by_stage: dict[str, int] = {}
    open_jobs = 0
    closed_jobs = 0
    for row in materialised:
        stage = str(row.get("stage") or UNKNOWN_STAGE)
        # NOTE: despite the approved field name this is a COUNT of rows whose
        # persisted ``workflow_error_count`` is greater than zero, grouped by
        # stage. No denominator and no percentage is produced (X4-D3).
        if int(row.get("workflow_error_count") or 0) > 0:
            errors_by_stage[stage] = errors_by_stage.get(stage, 0) + 1
        if stage in OPEN_STAGES:
            open_jobs += 1
        elif stage in CLOSED_STAGES:
            closed_jobs += 1

    return {
        "failed_jobs": _count_stage(materialised, FAILED_STAGE),
        "retry_exhausted_jobs": sum(1 for row in materialised if is_retry_exhausted(row)),
        "stuck_locked_jobs": sum(
            1
            for row in materialised
            if is_stuck(row, now=now, stale_after_seconds=stale_after_seconds)
        ),
        "blocked_jobs": _count_stage(materialised, BLOCKED_STAGE),
        "manual_review_jobs": _count_stage(materialised, MANUAL_REVIEW_STAGE),
        "error_rate_by_stage": dict(sorted(errors_by_stage.items())),
        "queue_depth_by_stage": dict(stage_distribution(materialised)),
        "open_vs_closed": {"open": open_jobs, "closed": closed_jobs},
        "rows_examined": len(materialised),
        "read_limit": int(limit),
        "truncated": len(materialised) >= int(limit),
        "stale_after_seconds": int(stale_after_seconds),
    }


def _count_stage(rows: list[dict[str, Any]], stage: str) -> int:
    return sum(1 for row in rows if (row.get("stage") or "") == stage)


def aggregate_sla(
    *,
    configured: Optional[bool],
    sla_hours: Optional[int] = None,
    breached: Optional[int] = None,
) -> dict[str, Any]:
    """Compose the SLA metrics from the existing configured setting + flag.

    Authority (X2, reused verbatim here): the SLA value is the **configured**
    setting, and when that setting is absent the breach position is **not
    evaluable**. A missing configuration therefore yields ``not_configured`` with
    **no** breach figure and **no** SLA value — a fallback default must never be
    presented as an approved SLA, nor turned into a fabricated breach.

    ``configured is None`` means the settings read itself failed, which is
    reported honestly as ``unknown``.
    """
    if configured is None:
        return {
            "sla_configured": None,
            "sla_hours": None,
            "sla_breached_items": None,
            "sla_state": SLA_STATE_UNKNOWN,
        }
    if not configured:
        return {
            "sla_configured": False,
            "sla_hours": None,
            "sla_breached_items": None,
            "sla_state": SLA_STATE_NOT_CONFIGURED,
        }
    return {
        "sla_configured": True,
        "sla_hours": int(sla_hours) if sla_hours is not None else None,
        # Flag-only semantics (X4-D4): the persisted `sla_breached` signal.
        "sla_breached_items": int(breached or 0),
        "sla_state": SLA_STATE_CONFIGURED,
    }


def aggregate_worker_liveness(
    heartbeat: Optional[dict[str, Any]],
    *,
    now: Optional[datetime] = None,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Compose the worker-liveness metric (reuses X1's classifier verbatim).

    ``UNKNOWN`` when the worker has never ticked — reported as unknown, never as
    healthy. Included so failure figures are never read as "live" while the worker
    is dead.
    """
    tick = (heartbeat or {}).get("tick_at")
    liveness = classify_worker_liveness(
        tick, now=now, stale_after_seconds=stale_after_seconds
    )
    return {
        "state": liveness.get("state", HEARTBEAT_UNKNOWN),
        "age_seconds": liveness.get("age_seconds"),
        "last_tick": liveness.get("last_tick"),
        "worker_id": (heartbeat or {}).get("worker_id"),
        "stale_after_seconds": int(stale_after_seconds),
    }


# ---------------------------------------------------------------------------
# Read-only service (composition over existing repositories)
# ---------------------------------------------------------------------------


class OperationalIntelligenceService:
    """Composes the approved X4 metrics from existing persisted data.

    Read-only: nothing is written, no schema is touched, and no X2 alerting is
    evaluated or dispatched. Repository methods are the ones X1/X2 already use.
    """

    def __init__(self, repos: Any) -> None:
        self._repos = repos

    async def _queue_rows(self) -> list[dict[str, Any]]:
        """Rows backing the failure metrics (the existing X1 read path/bound)."""
        return await self._repos.processing.queue_visibility_rows(limit=QUEUE_READ_LIMIT)

    async def _sla(self) -> dict[str, Any]:
        """SLA metrics from the configured setting + the persisted breach flag.

        A settings read failure is reported as ``unknown`` rather than crashing the
        operator view or inventing a breach.
        """
        configured: Optional[bool] = None
        settings = None
        try:
            if hasattr(self._repos, "queue_settings"):
                configured = bool(await self._repos.queue_settings.is_configured())
                if configured:
                    settings = await self._repos.queue_settings.get_settings()
        except Exception as exc:  # noqa: BLE001 — reported honestly as `unknown`
            logger.warning("X4 SLA settings read failed: %s", type(exc).__name__)
            configured = None

        if configured is not True:
            return aggregate_sla(configured=configured)

        breached = int(await self._repos.processing.count_sla_breached())
        return aggregate_sla(
            configured=True,
            sla_hours=getattr(settings, "sla_hours", None) if settings else None,
            breached=breached,
        )

    async def failures(self) -> dict[str, Any]:
        """The approved failure/queue metrics only."""
        return aggregate_queue_rows(await self._queue_rows())

    async def sla(self) -> dict[str, Any]:
        """The approved SLA metrics only."""
        return await self._sla()

    async def summary(self) -> dict[str, Any]:
        """One structured payload: failures + SLA + worker liveness.

        Deliberately **window-less** (X4-D1): current-state counts only, no trend
        or time-window semantics. Contains no document contents, filenames, signed
        URLs, per-organisation breakdown or raw ``last_error`` text.
        """
        rows = await self._queue_rows()
        heartbeat = await self._repos.processing.latest_worker_heartbeat()
        sla = await self._sla()
        return {
            "scope": "internal",
            "x4_scope": X4_SCOPE,
            **aggregate_queue_rows(rows),
            **sla,
            "worker_liveness": aggregate_worker_liveness(heartbeat),
            # X4-D1: no trend/window section exists, by PO ruling.
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
