"""Phase 8-X X4 — operational intelligence aggregation tests.

Authority: the PO-approved bounded contract
``CARBONTALLY_PHASE8X_X4_AGGREGATION_CONTRACT_20260914.md`` and its rulings
(window-less X4-D1, explicit ``truncated`` X4-D2, no failure-rate X4-D3,
flag-only SLA X4-D4, one read-only endpoint X4-D5).

Pure tests only (no database, no HTTP): every metric is asserted against the
existing X1/X2 predicates so X4 cannot silently diverge from them.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from domain.operational_health import (
    DEFAULT_STALE_AFTER_SECONDS,
    HEARTBEAT_HEALTHY,
    HEARTBEAT_STALE,
    HEARTBEAT_UNKNOWN,
    summarise_queue,
)
from services.operational_intelligence import (
    QUEUE_READ_LIMIT,
    SLA_STATE_CONFIGURED,
    SLA_STATE_NOT_CONFIGURED,
    SLA_STATE_UNKNOWN,
    OperationalIntelligenceService,
    aggregate_queue_rows,
    aggregate_sla,
    aggregate_worker_liveness,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def row(**over) -> dict:
    base = {
        "id": "job",
        "organization_id": "org",
        "stage": "extracting",
        "status": "processing",
        "attempt_count": 0,
        "max_attempts": 3,
        "workflow_error_count": 0,
        "workflow_next_retry_at": None,
        "last_error": None,
        "locked_at": None,
        "lock_token": None,
        "created_at": NOW - timedelta(minutes=5),
        "ingested_at": NOW - timedelta(minutes=5),
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Every approved metric individually
# ---------------------------------------------------------------------------


def test_failed_jobs_counts_only_the_failed_stage() -> None:
    rows = [row(stage="failed"), row(stage="failed"), row(stage="completed")]
    assert aggregate_queue_rows(rows, now=NOW)["failed_jobs"] == 2


def test_retry_exhausted_uses_the_existing_x1_predicate() -> None:
    rows = [
        row(attempt_count=3, max_attempts=3),    # exhausted
        row(attempt_count=4, max_attempts=3),    # exhausted
        row(attempt_count=1, max_attempts=3),    # not exhausted
        row(attempt_count=None, max_attempts=3)  # unknown is never counted
    ]
    assert aggregate_queue_rows(rows, now=NOW)["retry_exhausted_jobs"] == 2


def test_stuck_locked_jobs_uses_the_existing_stale_window() -> None:
    stale = NOW - timedelta(seconds=DEFAULT_STALE_AFTER_SECONDS + 60)
    fresh = NOW - timedelta(seconds=10)
    rows = [
        row(lock_token="t1", locked_at=stale),  # stuck
        row(lock_token="t2", locked_at=fresh),  # fresh claim
        row(lock_token=None, locked_at=stale),  # never claimed
    ]
    assert aggregate_queue_rows(rows, now=NOW)["stuck_locked_jobs"] == 1


def test_blocked_and_manual_review_are_separate_buckets() -> None:
    rows = [row(stage="blocked"), row(stage="blocked"), row(stage="manual_review")]
    out = aggregate_queue_rows(rows, now=NOW)
    assert out["blocked_jobs"] == 2
    assert out["manual_review_jobs"] == 1
    assert out["failed_jobs"] == 0  # never merged into "failures"


def test_error_rate_by_stage_is_a_count_not_a_rate() -> None:
    rows = [
        row(stage="extracting", workflow_error_count=2),
        row(stage="extracting", workflow_error_count=1),
        row(stage="mapping", workflow_error_count=0),
        row(stage="failed", workflow_error_count=5),
    ]
    out = aggregate_queue_rows(rows, now=NOW)["error_rate_by_stage"]
    assert out == {"extracting": 2, "failed": 1}
    assert all(isinstance(v, int) for v in out.values())  # no percentage (X4-D3)


def test_queue_depth_by_stage_and_open_vs_closed() -> None:
    rows = [
        row(stage="queued"),
        row(stage="extracting"),
        row(stage="failed"),
        row(stage="completed"),
    ]
    out = aggregate_queue_rows(rows, now=NOW)
    assert out["queue_depth_by_stage"] == {
        "completed": 1, "extracting": 1, "failed": 1, "queued": 1,
    }
    assert out["open_vs_closed"] == {"open": 2, "closed": 2}


def test_rows_examined_and_read_limit_reported_honestly() -> None:
    out = aggregate_queue_rows([row()], now=NOW, limit=10)
    assert out["rows_examined"] == 1
    assert out["read_limit"] == 10
    assert out["truncated"] is False


def test_truncated_is_explicit_at_the_read_bound() -> None:
    """X4-D2 — a full read bound must never look like a complete population."""
    rows = [row() for _ in range(QUEUE_READ_LIMIT)]
    out = aggregate_queue_rows(rows, now=NOW)
    assert out["truncated"] is True
    assert out["read_limit"] == QUEUE_READ_LIMIT


def test_empty_queue_is_an_honest_zero_population() -> None:
    out = aggregate_queue_rows([], now=NOW)
    assert out["failed_jobs"] == 0
    assert out["retry_exhausted_jobs"] == 0
    assert out["error_rate_by_stage"] == {}
    assert out["open_vs_closed"] == {"open": 0, "closed": 0}
    assert out["truncated"] is False



# ---------------------------------------------------------------------------
# SLA — flag-only, and never fabricated (X4-D4)
# ---------------------------------------------------------------------------


def test_sla_configured_reports_the_setting_and_the_flag() -> None:
    out = aggregate_sla(configured=True, sla_hours=48, breached=3)
    assert out == {
        "sla_configured": True,
        "sla_hours": 48,
        "sla_breached_items": 3,
        "sla_state": SLA_STATE_CONFIGURED,
    }


def test_sla_not_configured_invents_no_value_and_no_breach() -> None:
    """A missing setting must never become an SLA figure or a breach."""
    out = aggregate_sla(configured=False)
    assert out["sla_state"] == SLA_STATE_NOT_CONFIGURED
    assert out["sla_configured"] is False
    assert out["sla_hours"] is None
    assert out["sla_breached_items"] is None


def test_sla_unknown_when_the_settings_read_fails() -> None:
    out = aggregate_sla(configured=None)
    assert out["sla_state"] == SLA_STATE_UNKNOWN
    assert out["sla_configured"] is None
    assert out["sla_breached_items"] is None


def test_sla_has_no_deadline_derived_semantic() -> None:
    """X4-D4 — no sla_deadline computation exists in this module."""
    out = aggregate_sla(configured=True, sla_hours=48, breached=0)
    assert set(out) == {
        "sla_configured", "sla_hours", "sla_breached_items", "sla_state",
    }


# ---------------------------------------------------------------------------
# Worker liveness
# ---------------------------------------------------------------------------


def test_worker_unknown_when_no_tick_was_ever_recorded() -> None:
    out = aggregate_worker_liveness(None, now=NOW)
    assert out["state"] == HEARTBEAT_UNKNOWN
    assert out["age_seconds"] is None
    assert out["worker_id"] is None


def test_worker_healthy_and_stale() -> None:
    healthy = aggregate_worker_liveness(
        {"tick_at": (NOW - timedelta(seconds=30)).isoformat(), "worker_id": "w1"},
        now=NOW,
    )
    stale = aggregate_worker_liveness(
        {"tick_at": (NOW - timedelta(seconds=900)).isoformat(), "worker_id": "w1"},
        now=NOW,
    )
    assert healthy["state"] == HEARTBEAT_HEALTHY
    assert stale["state"] == HEARTBEAT_STALE


# ---------------------------------------------------------------------------
# X4 / X1 consistency — the same rows must never be classified differently
# ---------------------------------------------------------------------------


def test_x4_counts_agree_with_the_x1_summary() -> None:
    rows = [
        row(stage="failed"),
        row(stage="blocked"),
        row(stage="manual_review"),
        row(attempt_count=3, max_attempts=3),
        row(lock_token="t", locked_at=NOW - timedelta(hours=1)),
        row(stage="completed"),
    ]
    x1 = summarise_queue(rows, now=NOW)
    x4 = aggregate_queue_rows(rows, now=NOW)

    assert x4["failed_jobs"] == x1["stage_distribution"].get("failed", 0)
    assert x4["blocked_jobs"] == x1["stage_distribution"].get("blocked", 0)
    assert x4["manual_review_jobs"] == x1["stage_distribution"].get("manual_review", 0)
    assert x4["stuck_locked_jobs"] == x1["stuck_claims"]
    assert x4["retry_exhausted_jobs"] == x1["retry_exhausted"]
    assert x4["queue_depth_by_stage"] == x1["stage_distribution"]
    assert x4["open_vs_closed"]["open"] == x1["open_jobs"]


# ---------------------------------------------------------------------------
# Redaction — no error text / filenames / PII in the payload
# ---------------------------------------------------------------------------


def test_payload_carries_no_error_text_filenames_or_emails() -> None:
    rows = [
        row(
            stage="failed",
            last_error="OCR failed for invoice sent to billing@customer.example.com",
            workflow_error_count=1,
        )
    ]
    payload = aggregate_queue_rows(rows, now=NOW)
    serialised = repr(payload)
    assert "billing@customer.example.com" not in serialised
    assert "last_error" not in serialised
    assert "OCR failed" not in serialised
    assert "file_name" not in serialised


# ---------------------------------------------------------------------------
# Service composition (stub repositories; no database)
# ---------------------------------------------------------------------------


class _StubProcessing:
    def __init__(
        self,
        rows: list[dict] | None = None,
        *,
        breached: int = 0,
        heartbeat: dict | None = None,
    ) -> None:
        self.rows = rows or []
        self.breached = breached
        self.heartbeat = heartbeat
        self.limits: list[int] = []
        self.breach_reads = 0

    async def queue_visibility_rows(self, *, limit: int = QUEUE_READ_LIMIT) -> list[dict]:
        self.limits.append(limit)
        return self.rows

    async def count_sla_breached(self) -> int:
        self.breach_reads += 1
        return self.breached

    async def latest_worker_heartbeat(self) -> dict | None:
        return self.heartbeat


class _StubQueueSettings:
    def __init__(self, *, configured: bool, sla_hours: int = 48, raises: bool = False) -> None:
        self._configured = configured
        self._sla_hours = sla_hours
        self._raises = raises

    async def is_configured(self) -> bool:
        if self._raises:
            raise RuntimeError("settings unavailable")
        return self._configured

    async def get_settings(self):
        from types import SimpleNamespace

        return SimpleNamespace(sla_hours=self._sla_hours)


class _StubRepos:
    def __init__(self, processing, queue_settings=None) -> None:
        self.processing = processing
        if queue_settings is not None:
            self.queue_settings = queue_settings


def _service(processing, queue_settings=None) -> OperationalIntelligenceService:
    return OperationalIntelligenceService(_StubRepos(processing, queue_settings))


def test_service_reads_the_existing_x1_bound() -> None:
    """X4 must read through X1's own bound so `truncated` is meaningful."""
    processing = _StubProcessing([row()])
    asyncio.run(_service(processing).summary())
    assert processing.limits == [QUEUE_READ_LIMIT]


def test_service_summary_configured_sla_and_all_approved_keys() -> None:
    processing = _StubProcessing(
        [row(stage="failed")],
        breached=2,
        heartbeat={"tick_at": (NOW - timedelta(seconds=5)).isoformat(), "worker_id": "w1"},
    )
    out = asyncio.run(
        _service(processing, _StubQueueSettings(configured=True, sla_hours=48)).summary()
    )
    assert set(out) >= {
        "failed_jobs", "retry_exhausted_jobs", "stuck_locked_jobs", "blocked_jobs",
        "manual_review_jobs", "error_rate_by_stage", "sla_configured", "sla_hours",
        "sla_breached_items", "sla_state", "queue_depth_by_stage", "open_vs_closed",
        "worker_liveness", "evaluated_at", "truncated", "scope", "x4_scope",
    }
    assert out["failed_jobs"] == 1
    assert out["sla_state"] == SLA_STATE_CONFIGURED
    assert out["sla_hours"] == 48
    assert out["sla_breached_items"] == 2
    assert out["scope"] == "internal"
    assert out["x4_scope"] == "failures_and_sla"


def test_service_does_not_even_read_breaches_when_sla_is_unconfigured() -> None:
    """A not-configured SLA must not be turned into a breach figure at all."""
    processing = _StubProcessing([row(stage="failed")], breached=7)
    out = asyncio.run(
        _service(processing, _StubQueueSettings(configured=False)).summary()
    )
    assert out["sla_state"] == SLA_STATE_NOT_CONFIGURED
    assert out["sla_breached_items"] is None
    assert processing.breach_reads == 0


def test_service_reports_unknown_when_settings_read_fails() -> None:
    processing = _StubProcessing([row()])
    out = asyncio.run(
        _service(processing, _StubQueueSettings(configured=True, raises=True)).summary()
    )
    assert out["sla_state"] == SLA_STATE_UNKNOWN
    assert out["sla_breached_items"] is None


def test_service_without_settings_repository_reports_unknown() -> None:
    processing = _StubProcessing([row()])
    out = asyncio.run(_service(processing).summary())
    assert out["sla_state"] == SLA_STATE_UNKNOWN


def test_service_truncation_and_worker_unknown_end_to_end() -> None:
    processing = _StubProcessing([row() for _ in range(QUEUE_READ_LIMIT)])
    out = asyncio.run(
        _service(processing, _StubQueueSettings(configured=True)).summary()
    )
    assert out["truncated"] is True
    assert out["worker_liveness"]["state"] == HEARTBEAT_UNKNOWN


def test_summary_is_window_less_by_ruling() -> None:
    """X4-D1 — no trend/time-window section may appear in the payload."""
    processing = _StubProcessing([row()])
    out = asyncio.run(_service(processing, _StubQueueSettings(configured=True)).summary())
    keys = " ".join(out).lower()
    # `error_rate_by_stage` is an approved field name (a count, X4-D3); what must
    # not exist is any trend/window/percentage semantic.
    for forbidden in ("trend", "window", "last_24h", "last_7d", "percent", "yesterday"):
        assert forbidden not in keys


def test_summary_is_redacted_end_to_end() -> None:
    processing = _StubProcessing(
        [
            row(
                stage="failed",
                last_error="Statement for ops@customer.example.com could not be parsed",
                workflow_error_count=1,
            )
        ]
    )
    out = asyncio.run(_service(processing, _StubQueueSettings(configured=True)).summary())
    serialised = repr(out)
    assert "ops@customer.example.com" not in serialised
    assert "last_error" not in serialised
    assert "file_url" not in serialised
    assert "signed" not in serialised.lower()


def test_summary_has_no_per_organisation_breakdown() -> None:
    processing = _StubProcessing(
        [row(organization_id="org-a"), row(organization_id="org-b")]
    )
    out = asyncio.run(_service(processing, _StubQueueSettings(configured=True)).summary())
    serialised = repr(out)
    assert "org-a" not in serialised
    assert "org-b" not in serialised
    assert "organization" not in " ".join(out).lower()


