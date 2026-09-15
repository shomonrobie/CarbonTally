"""Phase 8-X X2 — alert evaluation domain tests (pure; no database).

Locks the seven PO-approved X2 values (2026-09-14): the three conditions, the approved
thresholds, the one-alert-per-condition-per-hour cooldown, and the honest handling of
inputs that are absent or unconfigured.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.operational_alerts import (
    ALERT_LINK,
    BACKLOG_WAITING_THRESHOLD,
    CONDITION_QUEUE_BACKLOG,
    CONDITION_RETRY_EXHAUSTED,
    CONDITION_SLA_BREACH,
    CONDITION_WORKER_STALE,
    CONDITIONS,
    DELIVERY_MAX_ATTEMPTS,
    NOT_EVALUABLE_NOT_CONFIGURED,
    WORKER_STALE_SECONDS,
    AlertEvaluationViolation,
    cooldown_bucket,
    evaluate_alerts,
    event_key,
)

NOW = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)


def _fired(result, condition: str) -> bool:
    return result["decisions"][condition]["alerted"]


def _alerts_for(result, condition: str) -> list[dict]:
    return [a for a in result["alerts"] if a["condition"] == condition]


# ---------------------------------------------------------------------------
# Approved values (PX-6)
# ---------------------------------------------------------------------------


def test_approved_conditions_are_exactly_the_three() -> None:
    assert set(CONDITIONS) == {
        CONDITION_QUEUE_BACKLOG,
        CONDITION_WORKER_STALE,
        CONDITION_SLA_BREACH,
        CONDITION_RETRY_EXHAUSTED,
    }
    # Provider outage is excluded: it needs provider access, which PX-4 declined.
    assert "PROVIDER_OUTAGE" not in CONDITIONS


def test_approved_thresholds_are_the_po_values() -> None:
    assert BACKLOG_WAITING_THRESHOLD == 100
    assert WORKER_STALE_SECONDS == 15 * 60
    assert DELIVERY_MAX_ATTEMPTS == 3


def test_cooldown_key_is_one_per_condition_per_hour() -> None:
    # Same hour → same key (the DB unique index then suppresses the duplicate).
    assert event_key(CONDITION_QUEUE_BACKLOG, now=NOW) == event_key(
        CONDITION_QUEUE_BACKLOG, now=NOW + timedelta(minutes=59)
    )
    # Next hour → a new key, so a persisting problem can alert again.
    assert event_key(CONDITION_QUEUE_BACKLOG, now=NOW) != event_key(
        CONDITION_QUEUE_BACKLOG, now=NOW + timedelta(hours=1)
    )
    # Different conditions never share a key.
    assert event_key(CONDITION_QUEUE_BACKLOG, now=NOW) != event_key(
        CONDITION_WORKER_STALE, now=NOW
    )
    assert cooldown_bucket(NOW) == "20260914T12"


def test_unknown_condition_key_is_rejected() -> None:
    with pytest.raises(AlertEvaluationViolation):
        event_key("NOT_A_CONDITION", now=NOW)
