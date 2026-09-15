"""Phase 8-X X1 — operational health domain logic (pure, no I/O).

Bounded first release, per the PO decisions of 2026-09-14:
**worker/queue visibility** and **health/worker heartbeat** only. Runtime/deployment
introspection is deliberately excluded.

Authoritative basis — Phase 8-X discovery
``CARBONTALLY_PHASE8X_OPERATIONAL_INTELLIGENCE_DISCOVERY_AND_IMPLEMENTATION_BOUNDARY_20260912.md``:

* **M1** — *"Worker & queue operational visibility — backlog, stuck/claimed jobs,
  retry exhaustion, ``workflow_error_count``, ``last_error``, stage distribution,
  oldest-waiting age … All data already exists in ``document_processing_queue``;
  no schema change required."*
* **M2** — *"Health-path correctness + worker liveness — ``/health`` must exercise
  the pool path; expose worker heartbeat/last-tick."*

This module holds the *classification* rules only; the repository reads the rows and
the API authorizes. It introduces no new vocabulary: stages are the ones the queue
already persists, and the heartbeat state is derived from an explicit tick compared
against a declared staleness window.

The heartbeat is stored in the **existing** ``dashboard_metrics`` table (which has
``expires_at``); no schema change is introduced by X1.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Optional

# ---------------------------------------------------------------------------
# M1 — queue visibility
# ---------------------------------------------------------------------------

#: Heartbeat metric identity in ``dashboard_metrics`` (no new table).
HEARTBEAT_METRIC_TYPE = "OPERATIONAL_HEALTH"
HEARTBEAT_METRIC_NAME = "WORKER_HEARTBEAT"

#: Default staleness window. A tick older than this is STALE. Declaring the value is a
#: visibility rule, not a product threshold — ``PX-2`` alerting thresholds belong to X2
#: and are NOT decided here.
DEFAULT_STALE_AFTER_SECONDS = 300

#: Queue states that count as "waiting for work" (not yet finished either way).
OPEN_STAGES: tuple[str, ...] = (
    "queued",
    "ingesting",
    "extracting",
    "mapping",
    "validating",
    "calculating",
    "review",
    "blocked",
    "manual_review",
)

#: Work that has finished, successfully or not.
CLOSED_STAGES: tuple[str, ...] = ("completed", "failed")


class OperationalHealthViolation(ValueError):
    """Raised when operational-health input cannot be interpreted honestly."""


def _as_datetime(value: Any) -> Optional[datetime]:
    """Coerce a DB timestamp, or an ISO-8601 string, to an aware datetime.

    Strings are accepted because the heartbeat is read back out of a JSONB metric
    payload rather than a timestamp column. An unparseable value raises rather than
    being treated as "no tick", so a malformed tick can never be silently reported
    as UNKNOWN (which would hide a real fault).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise OperationalHealthViolation(
                f"unsupported timestamp value {value!r}"
            ) from exc
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    raise OperationalHealthViolation(f"unsupported timestamp value {value!r}")


def seconds_since(value: Any, *, now: datetime) -> Optional[int]:
    """Whole seconds between ``value`` and ``now`` (``None`` when unknown).

    Negative results are clamped to ``0`` so clock skew never reports a future age.
    """
    moment = _as_datetime(value)
    if moment is None:
        return None
    delta = (now - moment).total_seconds()
    return int(delta) if delta > 0 else 0


def is_stuck(row: dict[str, Any], *, now: datetime, stale_after_seconds: int) -> bool:
    """Whether a claimed job's lock has been held longer than the stale window.

    ``locked_at`` + ``lock_token`` are the existing claim markers; a job is stuck when
    it holds a lock past the same window ``release_stale_locks`` uses.
    """
    if not row.get("lock_token"):
        return False
    age = seconds_since(row.get("locked_at"), now=now)
    return age is not None and age >= stale_after_seconds


def is_retry_exhausted(row: dict[str, Any]) -> bool:
    """Whether the job has used all its attempts (``attempt_count`` >= ``max_attempts``)."""
    attempts = row.get("attempt_count")
    maximum = row.get("max_attempts")
    if attempts is None or maximum is None:
        return False
    return int(attempts) >= int(maximum)


def stage_distribution(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count rows per persisted ``stage`` (missing stage grouped as ``UNKNOWN``)."""
    out: dict[str, int] = {}
    for row in rows:
        stage = str(row.get("stage") or "UNKNOWN")
        out[stage] = out.get(stage, 0) + 1
    return dict(sorted(out.items()))


def summarise_queue(
    rows: Iterable[dict[str, Any]],
    *,
    now: Optional[datetime] = None,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Build the M1 visibility summary from persisted queue rows.

    Every number is derived from fields the queue already stores; no row is counted
    twice and ``oldest_waiting_age_seconds`` considers only jobs in an open stage, so
    completed work never inflates the backlog age.
    """
    now = now or datetime.now(timezone.utc)
    if stale_after_seconds <= 0:
        raise OperationalHealthViolation("stale_after_seconds must be positive")

    materialised = list(rows)
    open_rows = [r for r in materialised if (r.get("stage") or "") in OPEN_STAGES]
    stuck = [r for r in materialised if is_stuck(r, now=now, stale_after_seconds=stale_after_seconds)]
    exhausted = [r for r in materialised if is_retry_exhausted(r)]
    with_errors = [r for r in materialised if r.get("last_error")]

    waiting_ages = [
        age
        for age in (
            seconds_since(r.get("ingested_at") or r.get("created_at"), now=now) for r in open_rows
        )
        if age is not None
    ]

    return {
        "total_jobs": len(materialised),
        "open_jobs": len(open_rows),
        "stage_distribution": stage_distribution(materialised),
        "stuck_claims": len(stuck),
        "retry_exhausted": len(exhausted),
        "jobs_with_last_error": len(with_errors),
        "workflow_error_count": sum(int(r.get("workflow_error_count") or 0) for r in materialised),
        "oldest_waiting_age_seconds": max(waiting_ages) if waiting_ages else None,
        "stale_after_seconds": stale_after_seconds,
    }


# ---------------------------------------------------------------------------
# M2 — worker liveness (reuse of the existing ``dashboard_metrics`` store)
# ---------------------------------------------------------------------------

HEARTBEAT_HEALTHY = "HEALTHY"
HEARTBEAT_STALE = "STALE"
HEARTBEAT_UNKNOWN = "UNKNOWN"


def classify_worker_liveness(
    last_tick: Any,
    *,
    now: Optional[datetime] = None,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Classify the worker's liveness from its most recent heartbeat tick.

    ``UNKNOWN`` when no tick was ever recorded — the honest answer, never reported as
    healthy. This reports liveness only; it raises no alert and takes no action
    (alerting is X2 and its recipients/thresholds are PO decisions).
    """
    now = now or datetime.now(timezone.utc)
    if stale_after_seconds <= 0:
        raise OperationalHealthViolation("stale_after_seconds must be positive")

    age = seconds_since(last_tick, now=now)
    if age is None:
        state = HEARTBEAT_UNKNOWN
    elif age >= stale_after_seconds:
        state = HEARTBEAT_STALE
    else:
        state = HEARTBEAT_HEALTHY
    return {
        "state": state,
        "last_tick": _as_datetime(last_tick).isoformat() if _as_datetime(last_tick) else None,
        "age_seconds": age,
        "stale_after_seconds": stale_after_seconds,
    }

