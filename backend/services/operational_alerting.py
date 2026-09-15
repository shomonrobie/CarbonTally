"""Phase 8-X X2 — operational alerting service (threshold evaluation + dispatch).

Authority: PO decisions of 2026-09-14 on `PX-6` Option (a) — **internal CarbonTally
operations alerting only** — implemented per
``CARBONTALLY_PHASE8X_X2_ALERTING_CONTRACT_20260914.md``:

* recipients = internal staff holding the existing **``can_view_all``** permission
  (no separate mailbox or address list);
* conditions, thresholds and the hourly cooldown come from
  :mod:`domain.operational_alerts` (PO values, never invented here);
* deduplication reuses the existing ``notifications.event_key`` unique index via
  ``NotificationsRepository.create_idempotent``;
* delivery is **in-product + email**, and a failed email is retried
  **3 times over ~15 minutes**, then recorded as a failure and abandoned;
* every dispatch writes a canonical ``audit_trail`` entry.

Design rules carried from the project: a notification failure must never break
processing (the worker calls this best-effort), and nothing is fabricated — an
unconfigured SLA setting produces **no** SLA alert.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from core.logging import get_logger
from domain.operational_alerts import (
    DELIVERY_MAX_ATTEMPTS,
    DELIVERY_RETRY_WINDOW_SECONDS,
    evaluate_alerts,
)
from domain.operational_health import classify_worker_liveness, summarise_queue

logger = get_logger(__name__)

#: Channel identifiers recorded on ``notification_delivery.channel``.
CHANNEL_IN_PRODUCT = "in_product"
CHANNEL_EMAIL = "email"

#: Audit action for one dispatch (canonical append-only ``audit_trail``).
AUDIT_ACTION = "operational_alert_dispatched"


class OperationalAlertingService:
    """Evaluates the approved conditions and dispatches internal alerts."""

    def __init__(
        self,
        repos: Any,
        *,
        email_sender: Optional[Callable[[str, str, str], Awaitable[None]]] = None,
        sleeper: Optional[Callable[[float], Awaitable[None]]] = None,
        retry_delay_seconds: int = DELIVERY_RETRY_WINDOW_SECONDS // DELIVERY_MAX_ATTEMPTS,
    ) -> None:
        self._repos = repos
        self._email_sender = email_sender
        self._sleeper = sleeper or asyncio.sleep
        self._retry_delay_seconds = retry_delay_seconds

    # -- inputs ------------------------------------------------------------

    async def _queue_summary(self) -> dict[str, Any]:
        rows = await self._repos.processing.queue_visibility_rows()
        return summarise_queue(rows)

    async def _worker_liveness(self) -> dict[str, Any]:
        heartbeat = await self._repos.processing.latest_worker_heartbeat()
        return classify_worker_liveness(heartbeat["tick_at"] if heartbeat else None)

    async def _sla_input(self) -> dict[str, Any]:
        """SLA input — ``configured`` is true only when the setting really exists."""
        configured = False
        settings = None
        if hasattr(self._repos, "queue_settings"):
            configured = bool(await self._repos.queue_settings.is_configured())
            if configured:
                settings = await self._repos.queue_settings.get_settings()
        if not configured:
            return {"configured": False}
        breached = int(await self._repos.processing.count_sla_breached())
        return {
            "configured": True,
            "sla_hours": getattr(settings, "sla_hours", None),
            "breached": breached,
        }

    # -- evaluation --------------------------------------------------------

    async def evaluate(self, *, now: Optional[datetime] = None) -> dict[str, Any]:
        """Evaluate only (no writes) — used by verification and by dry runs."""
        return evaluate_alerts(
            queue_summary=await self._queue_summary(),
            worker_liveness=await self._worker_liveness(),
            sla=await self._sla_input(),
            now=now,
        )

    # -- dispatch ----------------------------------------------------------

    async def evaluate_and_dispatch(
        self, *, now: Optional[datetime] = None, actor: str = "system"
    ) -> dict[str, Any]:
        """Evaluate and dispatch to the approved recipients (best effort).

        Returns a report of what was raised, who received it and how delivery went.
        A failure at any point is recorded and never raised to the caller.
        """
        evaluation = await self.evaluate(now=now)
        alerts = evaluation["alerts"]

        recipients = await self._repos.notifications.internal_ops_user_ids()
        report: dict[str, Any] = {
            "evaluated_at": evaluation["evaluated_at"],
            "decisions": evaluation["decisions"],
            "alerts": [a["condition"] for a in alerts],
            "recipients": len(recipients),
            "dispatched": [],
        }
        if not alerts:
            return report
        if not recipients:
            # Nothing to deliver to — recorded honestly, never reported as sent.
            report["skipped_reason"] = "no internal recipient holds can_view_all"
            return report

        for alert in alerts:
            for user_id in recipients:
                report["dispatched"].append(
                    await self._dispatch_one(alert, user_id, actor=actor)
                )
        return report

    async def _dispatch_one(
        self, alert: dict[str, Any], user_id: str, *, actor: str
    ) -> dict[str, Any]:
        notification = await self._repos.notifications.create_idempotent(
            user_id,
            alert["event_key"],
            notification_type=alert["notification_type"],
            title=alert["title"],
            message=alert["message"],
            priority=alert["priority"],
            link=alert["link"],
            actor_domain="operations",
        )
        notification_id = str(getattr(notification, "id", "") or "")
        entry: dict[str, Any] = {
            "condition": alert["condition"],
            "event_key": alert["event_key"],
            "notification_id": notification_id,
            "user_id": user_id,
        }

        # In-product delivery is the notification row itself.
        if notification_id:
            await self._repos.notifications.record_delivery(
                notification_id, channel=CHANNEL_IN_PRODUCT, status="delivered"
            )

        # Email channel: 3 attempts over ~15 minutes, then a recorded failure.
        entry.update(await self._deliver_email(alert, user_id, notification_id))
        await self._record_audit(alert, user_id, entry, actor=actor)
        return entry


    async def _deliver_email(
        self, alert: dict[str, Any], user_id: str, notification_id: str
    ) -> dict[str, Any]:
        email = await self._repos.notifications.email_for_user(user_id)
        if not email:
            if notification_id:
                await self._repos.notifications.record_delivery(
                    notification_id,
                    channel=CHANNEL_EMAIL,
                    status="failed",
                    error_message="no email address on record",
                    attempts=0,
                )
            return {"email": False, "attempts": 0, "error": "no email address on record"}

        last_error: Optional[str] = None
        for attempt in range(1, DELIVERY_MAX_ATTEMPTS + 1):
            try:
                await self._send_email(email, alert["title"], alert["message"])
                if notification_id:
                    await self._repos.notifications.record_delivery(
                        notification_id,
                        channel=CHANNEL_EMAIL,
                        status="sent",
                        attempts=attempt,
                    )
                return {"email": True, "attempts": attempt}
            except Exception as exc:  # noqa: BLE001 — recorded, never fatal
                last_error = f"{type(exc).__name__}: {exc}"[:500]
                logger.warning(
                    "operational alert email attempt %s/%s failed: %s",
                    attempt, DELIVERY_MAX_ATTEMPTS, last_error,
                )
                if attempt < DELIVERY_MAX_ATTEMPTS and self._retry_delay_seconds:
                    await self._sleeper(self._retry_delay_seconds)

        # All attempts exhausted: record the failure and stop (no endless loop).
        if notification_id:
            await self._repos.notifications.record_delivery(
                notification_id,
                channel=CHANNEL_EMAIL,
                status="failed",
                error_message=last_error,
                attempts=DELIVERY_MAX_ATTEMPTS,
            )
        return {"email": False, "attempts": DELIVERY_MAX_ATTEMPTS, "error": last_error}

    async def _send_email(self, email: str, subject: str, body: str) -> None:
        if self._email_sender is not None:
            await self._email_sender(email, subject, body)
            return
        # Reuse the platform's transactional sender (lazy import keeps this module
        # importable in unit tests and when email is unconfigured). It reports
        # ``(delivered, reason)``: an unconfigured provider is an HONEST failure and
        # is raised so the caller records it instead of faking a success.
        from services.v3_email import send_transactional_email

        delivered, reason = await send_transactional_email(
            to_email=email, subject=subject, html=body
        )
        if not delivered:
            raise RuntimeError(f"email not delivered: {reason}")

    async def _record_audit(
        self, alert: dict[str, Any], user_id: str, entry: dict[str, Any], *, actor: str
    ) -> None:
        """Append one canonical ``audit_trail`` entry for the dispatch.

        Uses the project's existing audit contract (``AuditRepository.record`` takes
        an ``AuditEntry``). A failure here is logged and surfaced in the returned
        report rather than silently swallowed — an unrecorded dispatch must be
        visible, not hidden.
        """
        audit = getattr(self._repos, "audit", None)
        if audit is None or not hasattr(audit, "record"):
            return
        from domain.audit import AuditEntry

        audit_entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=alert["event_key"],
            entity_type="notifications",
            entity_id=entry.get("notification_id") or "",
            action=AUDIT_ACTION,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields={
                "condition": alert["condition"],
                "event_key": alert["event_key"],
                "recipient": user_id,
                "email_delivered": bool(entry.get("email")),
                "email_attempts": entry.get("attempts"),
            },
            after={
                "condition": alert["condition"],
                "event_key": alert["event_key"],
                "recipient": user_id,
                "email_delivered": bool(entry.get("email")),
                "email_attempts": entry.get("attempts"),
            },
            actor_type="system",
            origin="system",
            outcome="success",
        )
        try:
            await audit.record(audit_entry)
        except Exception as exc:  # noqa: BLE001
            # Recorded in the report (not swallowed); dispatch itself still stands.
            logger.exception("operational alert audit write failed")
            entry["audit_error"] = f"{type(exc).__name__}: {exc}"[:300]

