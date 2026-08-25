"""Notifications repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``notifications`` table (user-facing in-app messages).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository
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
            priority,
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
