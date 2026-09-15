"""Phase 8-X X2 — alert evaluation domain (pure, no I/O).

Bounded first release. Authority: PO decisions of 2026-09-14 on **`PX-6` Option (a)**
(alert **internal CarbonTally operations only**) and **`PX-7` Option (d)** (telemetry
detail retained 90 days, aggregates indefinitely), implemented per the bounded contract
`CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md`.

Approved alert conditions (`X2-D1`) — all three:

* **`QUEUE_BACKLOG`** — more than the approved number of jobs waiting;
* **`WORKER_STALE`** — no worker heartbeat within the approved window;
* **`RETRY_EXHAUSTED`** — jobs that have used all their attempts.

The contract's fourth candidate (provider outage) stays **excluded** — it needs provider
access, which `PX-4` declined.

**Thresholds are PO-SUPPLIED values for this release, not implementation choices.**
`PX-6` explicitly forbade invented thresholds, so the approved numbers live here as named
constants with their source recorded. Making them runtime-configurable would need a
settings column — a **schema change requiring separate authorisation** (contract §5.2);
until then they are constants, and they are never inferred from other data.

SLA breach is deliberately **not** given a numeric threshold here: the PO ruled
*"SLA breach: use the existing configured SLA setting"*. If that setting is absent, the
condition is reported as **not evaluable** and raises **no alert** — a missing
configuration must never be turned into a fabricated breach.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

# ---------------------------------------------------------------------------
# PO-supplied thresholds (PX-6, 2026-09-14) — NOT invented, NOT inferred
# ---------------------------------------------------------------------------

#: "backlog: more than 100 waiting jobs".
BACKLOG_WAITING_THRESHOLD = 100

#: "worker stale: more than 15 minutes without a heartbeat".
WORKER_STALE_SECONDS = 900

#: "maximum one alert per condition per hour" (cooldown/deduplication).
ALERT_COOLDOWN_SECONDS = 3600

#: "retry 3 times over approximately 15 minutes, then record the delivery failure and stop".
DELIVERY_MAX_ATTEMPTS = 3
DELIVERY_RETRY_WINDOW_SECONDS = 900

# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------

CONDITION_QUEUE_BACKLOG = "QUEUE_BACKLOG"
CONDITION_WORKER_STALE = "WORKER_STALE"
CONDITION_SLA_BREACH = "SLA_BREACH"
CONDITION_RETRY_EXHAUSTED = "RETRY_EXHAUSTED"

#: Every condition this release may raise. Provider outage is deliberately absent (`PX-4`).
CONDITIONS: tuple[str, ...] = (
    CONDITION_QUEUE_BACKLOG,
    CONDITION_WORKER_STALE,
    CONDITION_SLA_BREACH,
    CONDITION_RETRY_EXHAUSTED,
)

#: ``notification_type`` per condition (free-form column; mirrors the existing
#: consultant-lifecycle convention of one stable value per event).
NOTIFICATION_TYPE: dict[str, str] = {
    CONDITION_QUEUE_BACKLOG: "ops_alert_queue_backlog",
    CONDITION_WORKER_STALE: "ops_alert_worker_stale",
    CONDITION_SLA_BREACH: "ops_alert_sla_breach",
    CONDITION_RETRY_EXHAUSTED: "ops_alert_retry_exhausted",
}

#: In-product link for every operational alert (an existing authenticated route).
ALERT_LINK = "/ops/operational-health"

#: Priority is a ranking, not a severity vocabulary: worker-down outranks a backlog.
ALERT_PRIORITY: dict[str, int] = {
    CONDITION_WORKER_STALE: 3,
    CONDITION_QUEUE_BACKLOG: 2,
    CONDITION_RETRY_EXHAUSTED: 2,
    CONDITION_SLA_BREACH: 2,
}

#: Per-condition single-line headline (the message body carries the measured value).
ALERT_TITLE: dict[str, str] = {
    CONDITION_QUEUE_BACKLOG: "Processing backlog above threshold",
    CONDITION_WORKER_STALE: "Processing worker has stopped reporting",
    CONDITION_SLA_BREACH: "Processing SLA breach recorded",
    CONDITION_RETRY_EXHAUSTED: "Processing jobs have exhausted their retries",
}


class AlertEvaluationViolation(ValueError):
    """Raised when alert input cannot be interpreted honestly."""


# ---------------------------------------------------------------------------
# Deduplication / cooldown (reuses the project's ``event_key`` mechanism)
# ---------------------------------------------------------------------------


def cooldown_bucket(now: datetime) -> str:
    """The hourly bucket a condition's alert belongs to (UTC)."""
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H")


def event_key(condition: str, *, now: datetime) -> str:
    """Deterministic per-(condition, hour) key used for cooldown **and** dedup.

    Because the key is stable within the hour, the database's existing unique index on
    ``(recipient_id, event_key)`` (``uq_notifications_event_key``) enforces the approved
    *"one alert per condition per hour"* rule without any application-level state: a
    second evaluation in the same hour cannot create a duplicate alert for a recipient.
    """
    if condition not in CONDITIONS:
        raise AlertEvaluationViolation(f"unknown alert condition {condition!r}")
    return f"ops-alert::{condition}::{cooldown_bucket(now)}"


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

#: Reasons a condition did not alert (kept distinct so a gap is never read as "fine").
NOT_EVALUABLE_NOT_CONFIGURED = "not configured"
NOT_EVALUABLE_NO_DATA = "no data"


def _candidate(
    condition: str, *, now: datetime, message: str, measured: Any
) -> dict[str, Any]:
    return {
        "condition": condition,
        "event_key": event_key(condition, now=now),
        "notification_type": NOTIFICATION_TYPE[condition],
        "title": ALERT_TITLE[condition],
        "message": message,
        "priority": ALERT_PRIORITY[condition],
        "link": ALERT_LINK,
        "measured": measured,
    }


def evaluate_alerts(
    *,
    queue_summary: Optional[dict[str, Any]] = None,
    worker_liveness: Optional[dict[str, Any]] = None,
    sla: Optional[dict[str, Any]] = None,
    now: Optional[datetime] = None,
    backlog_threshold: int = BACKLOG_WAITING_THRESHOLD,
    worker_stale_seconds: int = WORKER_STALE_SECONDS,
) -> dict[str, Any]:
    """Evaluate the three approved conditions and return alerts plus a decisions map.

    Returns ``{"alerts": [...], "decisions": {condition: {...}}}``. Every condition is
    reported in ``decisions`` — including one that did **not** fire — so an operator (and
    this task's verification) can see *why* nothing was raised. A condition whose input is
    absent or unconfigured is ``evaluable: False``; that is never reported as healthy.
    """
    now = now or datetime.now(timezone.utc)
    alerts: list[dict[str, Any]] = []
    decisions: dict[str, dict[str, Any]] = {}

    # --- QUEUE_BACKLOG -----------------------------------------------------
    if queue_summary is None:
        decisions[CONDITION_QUEUE_BACKLOG] = {
            "evaluable": False, "reason": NOT_EVALUABLE_NO_DATA, "alerted": False,
        }
    else:
        waiting = int(queue_summary.get("open_jobs") or 0)
        fired = waiting > backlog_threshold
        decisions[CONDITION_QUEUE_BACKLOG] = {
            "evaluable": True, "alerted": fired,
            "measured": waiting, "threshold": backlog_threshold,
        }
        if fired:
            alerts.append(
                _candidate(
                    CONDITION_QUEUE_BACKLOG, now=now, measured=waiting,
                    message=(
                        f"{waiting} jobs are waiting in the processing queue "
                        f"(threshold: more than {backlog_threshold})."
                    ),
                )
            )

    # --- WORKER_STALE ------------------------------------------------------
    if worker_liveness is None:
        decisions[CONDITION_WORKER_STALE] = {
            "evaluable": False, "reason": NOT_EVALUABLE_NO_DATA, "alerted": False,
        }
    else:
        age = worker_liveness.get("age_seconds")
        state = worker_liveness.get("state")
        if state == "UNKNOWN" or age is None:
            # Never proven alive. The absence of any heartbeat is itself alertable.
            fired = True
            detail = "no heartbeat has ever been recorded"
        else:
            age = int(age)
            fired = state == "STALE" or age > worker_stale_seconds
            detail = (
                f"last heartbeat was {age}s ago "
                f"(threshold: more than {worker_stale_seconds}s)"
            )
        decisions[CONDITION_WORKER_STALE] = {
            "evaluable": True, "alerted": fired, "measured": age,
            "threshold": worker_stale_seconds, "state": state,
        }
        if fired:
            alerts.append(
                _candidate(
                    CONDITION_WORKER_STALE, now=now, measured=age,
                    message=f"The processing worker is not reporting: {detail}.",
                )
            )

    # --- RETRY_EXHAUSTED ---------------------------------------------------
    if queue_summary is None:
        decisions[CONDITION_RETRY_EXHAUSTED] = {
            "evaluable": False, "reason": NOT_EVALUABLE_NO_DATA, "alerted": False,
        }
    else:
        exhausted = int(queue_summary.get("retry_exhausted") or 0)
        fired = exhausted > 0
        decisions[CONDITION_RETRY_EXHAUSTED] = {
            "evaluable": True, "alerted": fired, "measured": exhausted, "threshold": 1,
        }
        if fired:
            alerts.append(
                _candidate(
                    CONDITION_RETRY_EXHAUSTED, now=now, measured=exhausted,
                    message=(
                        f"{exhausted} job(s) have exhausted their retry attempts."
                    ),
                )
            )

    # --- SLA_BREACH (configured setting only) ------------------------------
    if sla is None or not sla.get("configured"):
        decisions[CONDITION_SLA_BREACH] = {
            "evaluable": False,
            "reason": NOT_EVALUABLE_NOT_CONFIGURED,
            "alerted": False,
            "detail": "the SLA setting is not configured; no breach is inferred",
        }
    else:
        breached = int(sla.get("breached") or 0)
        fired = breached > 0
        decisions[CONDITION_SLA_BREACH] = {
            "evaluable": True, "alerted": fired,
            "measured": breached, "sla_hours": sla.get("sla_hours"),
        }
        if fired:
            alerts.append(
                _candidate(
                    CONDITION_SLA_BREACH, now=now, measured=breached,
                    message=(
                        f"{breached} item(s) have breached the configured "
                        f"SLA of {sla.get('sla_hours')} hour(s)."
                    ),
                )
            )

    return {"alerts": alerts, "decisions": decisions, "evaluated_at": now.isoformat()}

