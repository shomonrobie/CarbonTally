"""Phase 8-X X2 — operational alerting integration verification (real database).

Covers the outstanding X2 verification items O1–O7 against a **disposable clone**
(F-046-1: the session fixture TRUNCATEs its target, so it must never point at a
persistent environment).

* O1 — end-to-end dispatch: a real evaluation raises an alert, the approved
  recipient receives an in-product notification and delivery rows are recorded;
* O2 — hourly deduplication via the existing ``event_key`` unique index;
* O3 — recipients limited to internal staff holding ``can_view_all``;
* O4 — email failure recorded after exactly 3 attempts (no endless retry);
* O5 — an audit entry per dispatch;
* O6 — telemetry retention prunes detail only (product notifications and the
  excluded business tables are untouched; dry-run is the default).
* O7 lives in ``tests/unit/workers`` (worker wiring) and is asserted here too.

Every test removes only the rows it created.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import asyncpg
import pytest

from domain.operational_alerts import CONDITION_WORKER_STALE
from services.operational_alerting import (
    CHANNEL_EMAIL,
    CHANNEL_IN_PRODUCT,
    OperationalAlertingService,
)
from services.retention import enforce_retention

pytestmark = pytest.mark.asyncio

T0 = datetime(2026, 9, 14, 9, 0, 0, tzinfo=timezone.utc)
_ALERT_PREFIX = "ops_alert_"
_TEST_TYPE = "unit_test_marker"


async def _seed_staff(pool: asyncpg.Pool, *, can_view_all: bool, entity_id=None, with_email=True):
    """Create one user + role + staff profile; returns (user_id, email)."""
    user_id = str(uuid.uuid4())
    email = f"x2-{user_id[:8]}@test.local"
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            email if with_email else None,
        )
        role_id = await conn.fetchval(
            "INSERT INTO public.staff_roles (name, permissions) "
            "VALUES ($1, $2::jsonb) RETURNING id",
            f"x2-role-{uuid.uuid4().hex[:8]}",
            '{"can_view_all": true}' if can_view_all else '{"can_review": true}',
        )
        await conn.execute(
            "INSERT INTO public.staff_profiles "
            "(user_id, role_id, entity_id, first_name, last_name, email, is_active) "
            "VALUES ($1, $2, $3, 'X2', 'Tester', $4, true)",
            user_id,
            role_id,
            entity_id,
            email,
        )
    return user_id, email


async def _seed_processing_entity(pool: asyncpg.Pool) -> str:
    """A real processing-entity row (``staff_profiles.entity_id`` is an FK)."""
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.processing_entities (name) VALUES ($1) RETURNING id",
                f"X2 PE {uuid.uuid4().hex[:8]}",
            )
        )


async def _cleanup(pool: asyncpg.Pool, user_ids: list[str]) -> None:
    """Remove only what these tests created, in FK-safe order."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.notification_delivery WHERE notification_id IN "
            "(SELECT id FROM public.notifications WHERE recipient_id = ANY($1::uuid[]))",
            user_ids,
        )
        await conn.execute(
            "DELETE FROM public.notifications WHERE recipient_id = ANY($1::uuid[])",
            user_ids,
        )
        await conn.execute(
            "DELETE FROM public.audit_trail WHERE performed_by = ANY($1::uuid[])",
            user_ids,
        )
        await conn.execute(
            "DELETE FROM public.staff_profiles WHERE user_id = ANY($1::uuid[])",
            user_ids,
        )
        # Roles are only removed when nothing references them any more.
        await conn.execute(
            "DELETE FROM public.staff_roles r WHERE r.name LIKE 'x2-role-%' "
            "AND NOT EXISTS (SELECT 1 FROM public.staff_profiles p WHERE p.role_id = r.id)"
        )
        await conn.execute("DELETE FROM public.users WHERE id = ANY($1::uuid[])", user_ids)
        await conn.execute(
            "DELETE FROM public.processing_entities WHERE name LIKE 'X2 PE %'"
        )


async def _clear_heartbeat(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.dashboard_metrics WHERE metric_name = 'WORKER_HEARTBEAT'"
        )



# ---------------------------------------------------------------------------
# O1 / O2 / O3 / O5 — dispatch, dedup, recipients, audit
# ---------------------------------------------------------------------------


async def test_x2_dispatch_reaches_only_internal_can_view_all_with_dedup(
    pool: asyncpg.Pool,
) -> None:
    from api.dependencies import get_repositories

    repos = await get_repositories()
    included, _ = await _seed_staff(pool, can_view_all=True)
    excluded_no_perm, _ = await _seed_staff(pool, can_view_all=False)
    excluded_entity, _ = await _seed_staff(
        pool, can_view_all=True, entity_id=await _seed_processing_entity(pool)
    )
    sent: list[tuple[str, str, str]] = []

    async def _ok_sender(email: str, subject: str, body: str) -> None:
        sent.append((email, subject, body))

    service = OperationalAlertingService(
        repos, email_sender=_ok_sender, retry_delay_seconds=0
    )
    try:
        # No heartbeat exists on a fresh clone ⇒ liveness UNKNOWN ⇒ WORKER_STALE.
        await _clear_heartbeat(pool)

        # --- O3: the recipient set is exactly the internal can_view_all staff ---
        recipients = await repos.notifications.internal_ops_user_ids()
        assert included in recipients
        assert excluded_no_perm not in recipients
        assert excluded_entity not in recipients

        # --- O1: a real evaluation raises the condition and dispatches ---
        evaluation = await service.evaluate(now=T0)
        assert evaluation["decisions"][CONDITION_WORKER_STALE]["alerted"] is True

        first = await service.evaluate_and_dispatch(now=T0, actor=included)
        assert first["alerts"] == [CONDITION_WORKER_STALE]
        assert {e["user_id"] for e in first["dispatched"]} == {included}
        assert sent, "the approved email channel must be used"

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, event_key, notification_type FROM public.notifications "
                "WHERE recipient_id = $1 AND notification_type LIKE $2",
                included,
                f"{_ALERT_PREFIX}%",
            )
            assert len(rows) == 1, "one alert per condition per hour"
            notification_id = rows[0]["id"]

            # O1 — in-product + email delivery rows recorded
            channels = await conn.fetch(
                "SELECT channel, status FROM public.notification_delivery "
                "WHERE notification_id = $1 ORDER BY channel",
                notification_id,
            )
            by_channel = {r["channel"]: r["status"] for r in channels}
            assert by_channel.get(CHANNEL_IN_PRODUCT) == "delivered"
            assert by_channel.get(CHANNEL_EMAIL) == "sent"

            # O5 — an attributable audit entry exists for the dispatch
            audit = await conn.fetchval(
                "SELECT count(*) FROM public.audit_trail "
                "WHERE action_type = 'operational_alert_dispatched' AND performed_by = $1::uuid",
                included,
            )
            assert audit >= 1

        # --- O2: a second evaluation in the SAME hour cannot duplicate ---
        await service.evaluate_and_dispatch(now=T0, actor=included)
        async with pool.acquire() as conn:
            same_hour = await conn.fetchval(
                "SELECT count(*) FROM public.notifications "
                "WHERE recipient_id = $1 AND notification_type LIKE $2",
                included,
                f"{_ALERT_PREFIX}%",
            )
        assert same_hour == 1, "dedup must suppress the repeat within the hour"

        # --- O2 (boundary): the NEXT hour may alert again ---
        await service.evaluate_and_dispatch(now=T0 + timedelta(hours=1), actor=included)
        async with pool.acquire() as conn:
            next_hour = await conn.fetchval(
                "SELECT count(*) FROM public.notifications "
                "WHERE recipient_id = $1 AND notification_type LIKE $2",
                included,
                f"{_ALERT_PREFIX}%",
            )
        assert next_hour == 2, "a new hour is a new event_key"

        # --- O3 (negative): the excluded identities received nothing ---
        async with pool.acquire() as conn:
            leaked = await conn.fetchval(
                "SELECT count(*) FROM public.notifications "
                "WHERE recipient_id = ANY($1::uuid[])",
                [excluded_no_perm, excluded_entity],
            )
        assert leaked == 0
    finally:
        await _cleanup(pool, [included, excluded_no_perm, excluded_entity])
        await _clear_heartbeat(pool)


# ---------------------------------------------------------------------------
# O4 — email failure: exactly 3 attempts, recorded, then abandoned
# ---------------------------------------------------------------------------


async def test_x2_email_failure_is_recorded_after_three_attempts(pool: asyncpg.Pool) -> None:
    from api.dependencies import get_repositories

    repos = await get_repositories()
    user_id, _ = await _seed_staff(pool, can_view_all=True)
    attempts: list[int] = []

    async def _always_fail(email: str, subject: str, body: str) -> None:
        attempts.append(1)
        raise RuntimeError("simulated provider outage")

    service = OperationalAlertingService(
        repos, email_sender=_always_fail, retry_delay_seconds=0
    )
    try:
        await _clear_heartbeat(pool)
        outcome = await service.evaluate_and_dispatch(now=T0, actor=user_id)
        entry = next(e for e in outcome["dispatched"] if e["user_id"] == user_id)

        assert len(attempts) == 3, "exactly three attempts, never an endless loop"
        assert entry["email"] is False and entry["attempts"] == 3
        assert entry["error"] and "simulated provider outage" in entry["error"]

        async with pool.acquire() as conn:
            failed = await conn.fetchrow(
                "SELECT status, error_message FROM public.notification_delivery "
                "WHERE notification_id = $1 AND channel = $2",
                entry["notification_id"],
                CHANNEL_EMAIL,
            )
        assert failed is not None
        assert failed["status"] == "failed"
        assert failed["error_message"] and "simulated provider outage" in failed["error_message"]
    finally:
        await _cleanup(pool, [user_id])
        await _clear_heartbeat(pool)



# ---------------------------------------------------------------------------
# O6 — telemetry retention prunes DETAIL only (configurable; dry-run default)
# ---------------------------------------------------------------------------


async def test_x2_retention_prunes_telemetry_detail_only(pool: asyncpg.Pool) -> None:
    from api.dependencies import get_repositories

    repos = await get_repositories()
    user_id, _ = await _seed_staff(pool, can_view_all=True)
    old = datetime.now(timezone.utc) - timedelta(days=30)
    fresh = datetime.now(timezone.utc) - timedelta(hours=1)
    try:
        async with pool.acquire() as conn:
            # an OLD operational alert (telemetry detail) that must be pruned …
            alert_id = await conn.fetchval(
                "INSERT INTO public.notifications "
                "(recipient_type, recipient_id, notification_type, title, message, "
                " created_at, event_key) "
                "VALUES ('user', $1, $2, 't', 'm', $3, $4) RETURNING id",
                user_id,
                f"{_ALERT_PREFIX}worker_stale",
                old,
                f"x2-retention-{uuid.uuid4().hex[:8]}",
            )
            await conn.execute(
                "INSERT INTO public.notification_delivery "
                "(notification_id, channel, status, created_at) VALUES ($1, $2, 'sent', $3)",
                alert_id,
                CHANNEL_EMAIL,
                old,
            )
            # … an OLD ordinary product notification that must SURVIVE …
            product_id = await conn.fetchval(
                "INSERT INTO public.notifications "
                "(recipient_type, recipient_id, notification_type, title, message, created_at) "
                "VALUES ('user', $1, $2, 't', 'm', $3) RETURNING id",
                user_id,
                _TEST_TYPE,
                old,
            )
            # … one old and one fresh telemetry metric row.
            await conn.execute(
                "INSERT INTO public.dashboard_metrics "
                "(metric_type, metric_name, metric_value, created_at) "
                "VALUES ('OPERATIONAL_HEALTH', 'X2_OLD', '{}'::jsonb, $1)",
                old,
            )
            await conn.execute(
                "INSERT INTO public.dashboard_metrics "
                "(metric_type, metric_name, metric_value, created_at) "
                "VALUES ('OPERATIONAL_HEALTH', 'X2_FRESH', '{}'::jsonb, $1)",
                fresh,
            )
            queue_before = await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue"
            )
            logs_before = await conn.fetchval("SELECT count(*) FROM public.processing_logs")

        # The duration is CONFIGURED, never hard-coded: set it to 1 day.
        await repos.settings.update_retention(
            audit_log_retention_days=None,
            data_retention_days=None,
            document_retention_days=None,
            backup_retention_days=None,
            operational_telemetry_retention_days=1,
            updated_by=None,
        )

        # Dry run is the default: nothing may be removed.
        dry = await enforce_retention(repos, dry_run=True)
        telemetry = dry["domains"]["operational_telemetry_retention_days"]
        assert telemetry["detail_retention_days"] == 1, "the configured value is used"
        assert "document_processing_queue" in telemetry["excluded_tables"]
        assert "processing_logs" in telemetry["excluded_tables"]
        assert telemetry["parts"]["alerts"]["eligible_notifications"] >= 1
        assert telemetry["parts"]["metrics"]["eligible_metrics"] >= 1
        async with pool.acquire() as conn:
            assert await conn.fetchval(
                "SELECT count(*) FROM public.notifications WHERE id = $1", alert_id
            ) == 1, "dry run must not delete"


        applied = await enforce_retention(repos, dry_run=False)
        assert applied["domains"]["operational_telemetry_retention_days"]["applied"] is True

        async with pool.acquire() as conn:
            assert await conn.fetchval(
                "SELECT count(*) FROM public.notifications WHERE id = $1", alert_id
            ) == 0, "expired operational alert telemetry is pruned"
            assert await conn.fetchval(
                "SELECT count(*) FROM public.notifications WHERE id = $1", product_id
            ) == 1, "ordinary product notifications are NEVER pruned"
            assert await conn.fetchval(
                "SELECT count(*) FROM public.dashboard_metrics WHERE metric_name = 'X2_OLD'"
            ) == 0, "expired telemetry detail is pruned"
            assert await conn.fetchval(
                "SELECT count(*) FROM public.dashboard_metrics WHERE metric_name = 'X2_FRESH'"
            ) == 1, "fresh telemetry is retained"
            assert await conn.fetchval(
                "SELECT count(*) FROM public.document_processing_queue"
            ) == queue_before, "PX-7 excluded table must be untouched"
            assert await conn.fetchval(
                "SELECT count(*) FROM public.processing_logs"
            ) == logs_before, "PX-7 excluded table must be untouched"
    finally:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM public.dashboard_metrics WHERE metric_name LIKE 'X2_%'"
            )
            await conn.execute(
                "DELETE FROM public.notification_delivery WHERE notification_id IN "
                "(SELECT id FROM public.notifications WHERE recipient_id = $1)",
                user_id,
            )
            await conn.execute(
                "DELETE FROM public.notifications WHERE recipient_id = $1", user_id
            )
        await _cleanup(pool, [user_id])
        # Restore the PO's approved initial value (90 days).
        await repos.settings.update_retention(
            audit_log_retention_days=None,
            data_retention_days=None,
            document_retention_days=None,
            backup_retention_days=None,
            operational_telemetry_retention_days=90,
            updated_by=None,
        )

