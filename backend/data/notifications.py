"""Notifications repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``notifications`` table (user-facing in-app messages).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb
from domain.operations import Notification

_NOTIF_COLUMNS = (
    "id, recipient_type, recipient_id, notification_type, title, message, "
    "priority, link, is_read, created_at"
)


def _row_to_notification(row: Any) -> Notification:
    r = dict(row)
    return Notification(
        id=str(r["id"]),
        recipient_type=str(r.get("recipient_type") or "user"),
        recipient_id=str(r.get("recipient_id") or ""),
        notification_type=r.get("notification_type"),
        title=r.get("title"),
        message=r.get("message"),
        priority=int(r.get("priority") or 0),
        link=r.get("link"),
        is_read=bool(r.get("is_read", False)),
        created_at=r.get("created_at"),
    )


class NotificationsRepository(AbstractRepository[Notification]):
    """CRUD and lookup for per-user notifications (real schema)."""

    async def list_for_user(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notification]:
        """Return the recipient's notifications, newest first.

        ``limit``/``offset`` bound the page (the API layer clamps ``limit`` to
        1..500); ordering is always ``created_at DESC`` for stable pagination.
        """
        query = (
            f"SELECT {_NOTIF_COLUMNS} FROM public.notifications "
            "WHERE recipient_type = 'user' AND recipient_id = $1"
        )
        if unread_only:
            query += " AND is_read = FALSE"
        query += " ORDER BY created_at DESC"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, user_id)
        return [_row_to_notification(r) for r in rows]

    async def count_for_user(self, user_id: str, unread_only: bool = False) -> int:
        """Total notifications for the recipient (used for pagination totals)."""
        query = (
            "SELECT COUNT(*) FROM public.notifications "
            "WHERE recipient_type = 'user' AND recipient_id = $1"
        )
        if unread_only:
            query += " AND is_read = FALSE"
        row = await self._fetch_one(query, user_id)
        return int(row[0]) if row is not None else 0

    async def create(
        self,
        user_id: str,
        *,
        notification_type: Optional[str] = None,
        title: Optional[str] = None,
        message: Optional[str] = None,
        priority: int = 0,
        link: Optional[str] = None,
    ) -> Notification:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.notifications (
                recipient_type, recipient_id, notification_type, title, message,
                priority, link, is_read, created_at
            ) VALUES ('user', $1, $2, $3, $4, $5, $6, FALSE, NOW())
            RETURNING {_NOTIF_COLUMNS}
            """,
            user_id,
            notification_type,
            title,
            message,
            str(priority),
            link,
        )
        if row is None:
            raise RuntimeError("notifications insert returned no row")
        return _row_to_notification(row)

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        status = await self._execute(
            "UPDATE public.notifications SET is_read = TRUE "
            "WHERE id = $1 AND recipient_type = 'user' AND recipient_id = $2",
            notification_id,
            user_id,
        )
        return "UPDATE 1" in status

    async def mark_all_read(self, user_id: str) -> None:
        await self._execute(
            "UPDATE public.notifications SET is_read = TRUE "
            "WHERE recipient_type = 'user' AND recipient_id = $1",
            user_id,
        )

    async def create_idempotent(
        self,
        user_id: str,
        event_key: str,
        *,
        notification_type: Optional[str] = None,
        title: Optional[str] = None,
        message: Optional[str] = None,
        priority: int = 0,
        link: Optional[str] = None,
        actor_domain: Optional[str] = None,
    ) -> Notification:
        """Create a recipient notification exactly once per ``event_key``.

        ``event_key`` is a deterministic per-(recipient, business-event)
        identifier supplied by the event producer; retries of the same event
        can never create duplicate notifications (unique partial index on
        ``(recipient_id, event_key) WHERE event_key IS NOT NULL``).
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.notifications (
                recipient_type, recipient_id, notification_type, title, message,
                priority, link, event_key, actor_domain, is_read, created_at
            ) VALUES ('user', $1, $2, $3, $4, $5::text, $6, $7, $8, FALSE, NOW())
            ON CONFLICT (recipient_id, event_key) WHERE event_key IS NOT NULL
            DO NOTHING
            RETURNING {_NOTIF_COLUMNS}
            """,
            user_id,
            notification_type,
            title,
            message,
            str(priority),
            link,
            event_key,
            actor_domain,
        )
        if row is None:
            existing = await self._fetch_one(
                f"SELECT {_NOTIF_COLUMNS} FROM public.notifications "
                "WHERE recipient_id = $1 AND event_key = $2 LIMIT 1",
                user_id,
                event_key,
            )
            return _row_to_notification(existing) if existing is not None else _row_to_notification(
                {"id": "", "recipient_type": "user", "recipient_id": user_id,
                 "notification_type": notification_type, "title": title,
                 "message": message, "priority": priority, "link": link,
                 "is_read": False, "created_at": None}
            )
        return _row_to_notification(row)

    async def support_staff_user_ids(self) -> list[str]:
        """Authorised CarbonTally Operations recipients for PE operational
        events: active INTERNAL staff whose role grants can_manage_staff."""
        rows = await self._fetch_all(
            "SELECT sp.user_id FROM public.staff_profiles sp "
            "JOIN public.staff_roles sr ON sr.id = sp.role_id "
            "WHERE sp.entity_id IS NULL AND coalesce(sp.is_active, true) = true "
            "AND coalesce((sr.permissions->>'can_manage_staff')::boolean, false) = true"
        )
        return [str(r["user_id"]) for r in rows]

    async def entity_participant_user_ids(
        self, conversation_id: str, entity_id: str, exclude_user: Optional[str] = None
    ) -> list[str]:
        """PE staff participants of an entity conversation (own entity only)."""
        rows = await self._fetch_all(
            "SELECT cp.user_id FROM public.conversation_participants cp "
            "JOIN public.staff_profiles sp ON sp.user_id = cp.user_id "
            "WHERE cp.conversation_id = $1 AND coalesce(cp.is_active, true) = true "
            "AND sp.entity_id = $2 AND coalesce(sp.is_active, true) = true "
            "AND ($3::uuid IS NULL OR cp.user_id <> $3)",
            conversation_id,
            entity_id,
            exclude_user,
        )
        return [str(r["user_id"]) for r in rows]

    async def get(self, id: str) -> Optional[Notification]:
        row = await self._fetch_one(
            f"SELECT {_NOTIF_COLUMNS} FROM public.notifications WHERE id = $1",
            id,
        )
        return _row_to_notification(row) if row is not None else None

    async def save(self, entity: Notification) -> Notification:
        return entity

    async def delete(self, id: str) -> None:
        return None

    # ------------------------------------------------------------------
    # Phase 8-X X2 — operational alerting support
    # ------------------------------------------------------------------

    async def internal_ops_user_ids(self) -> list[str]:
        """Active INTERNAL staff whose role grants ``can_view_all``.

        This is the PO-approved X2 recipient set (`PX-6` decision 3: "all internal
        staff with the existing view-all-operations permission"). No separate
        mailbox or address list is created, and processing-entity staff
        (``entity_id IS NOT NULL``) are excluded by construction.
        """
        rows = await self._fetch_all(
            "SELECT sp.user_id FROM public.staff_profiles sp "
            "JOIN public.staff_roles sr ON sr.id = sp.role_id "
            "WHERE sp.entity_id IS NULL AND coalesce(sp.is_active, true) = true "
            "AND coalesce((sr.permissions ->> 'can_view_all')::boolean, false) = true"
        )
        return [str(r["user_id"]) for r in rows]

    async def email_for_user(self, user_id: str) -> Optional[str]:
        """The user's email address, for the email delivery channel (may be absent)."""
        row = await self._fetch_one(
            "SELECT email FROM public.users WHERE id = $1", user_id
        )
        email = (row["email"] if row is not None else None) or None
        return str(email) if email else None

    async def record_delivery(
        self,
        notification_id: str,
        *,
        channel: str,
        status: str,
        error_message: Optional[str] = None,
        attempts: Optional[int] = None,
    ) -> None:
        """Record/refresh one delivery attempt outcome for a notification.

        Failures are recorded honestly (``status='failed'`` + ``error_message``);
        nothing is silently swallowed.
        """
        await self._execute(
            """
            INSERT INTO public.notification_delivery (
                notification_id, channel, status, sent_at, delivered_at,
                error_message, metadata, created_at, updated_at
            ) VALUES (
                $1::uuid, $2::text, $3::text,
                CASE WHEN $3::text IN ('sent', 'delivered') THEN NOW() END,
                CASE WHEN $3::text = 'delivered' THEN NOW() END,
                $4::text, $5::jsonb, NOW(), NOW()
            )
            """,
            notification_id,
            channel,
            status,
            error_message,
            dumps_jsonb({"attempts": attempts} if attempts is not None else {}),
        )

    async def prune_operational_alerts_before(
        self, cutoff: Any, *, dry_run: bool = True
    ) -> dict:
        """Retention for operational ALERT telemetry only (X2 / `PX-7`).

        Scope is deliberately narrow: notifications whose
        ``notification_type`` is an ``ops_alert_%`` operational alert, and their
        delivery rows. Ordinary product notifications are **never** touched, and
        neither is any report/evidence table.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                deliveries = await conn.fetchval(
                    "SELECT count(*) FROM public.notification_delivery d "
                    "JOIN public.notifications n ON n.id = d.notification_id "
                    "WHERE n.notification_type LIKE 'ops_alert_%' AND n.created_at < $1",
                    cutoff,
                )
                alerts = await conn.fetchval(
                    "SELECT count(*) FROM public.notifications "
                    "WHERE notification_type LIKE 'ops_alert_%' AND created_at < $1",
                    cutoff,
                )
                if not dry_run:
                    await conn.execute(
                        "DELETE FROM public.notification_delivery d USING public.notifications n "
                        "WHERE d.notification_id = n.id "
                        "AND n.notification_type LIKE 'ops_alert_%' AND n.created_at < $1",
                        cutoff,
                    )
                    await conn.execute(
                        "DELETE FROM public.notifications "
                        "WHERE notification_type LIKE 'ops_alert_%' AND created_at < $1",
                        cutoff,
                    )
        return {
            "domain": "operational_telemetry_retention_days",
            "scope": "operational alert notifications + deliveries (ops_alert_%)",
            "cutoff": cutoff.isoformat(),
            "eligible_notifications": int(alerts or 0),
            "eligible_deliveries": int(deliveries or 0),
            "applied": not dry_run,
        }
