"""V3 notifications surface (V3 legacy-capability reimplementation).

User-facing in-app notifications.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_auth

router = APIRouter(prefix="/api/v3/notifications", tags=["V3 — Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    # Bound the page: stable newest-first ordering (D26 scale hardening —
    # never load an unbounded per-user list into the browser).
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))
    rows = await repos.notifications.list_for_user(
        current_user.user_id, unread_only, limit=limit, offset=offset
    )
    return {
        "notifications": [
            {
                "id": n.id,
                "recipient_type": n.recipient_type,
                "recipient_id": n.recipient_id,
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "priority": n.priority,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in rows
        ],
        "total": await repos.notifications.count_for_user(
            current_user.user_id, unread_only
        ),
        "limit": limit,
        "offset": offset,
    }


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.notifications.mark_read(notification_id, current_user.user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification not found")
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    await repos.notifications.mark_all_read(current_user.user_id)
    return {"success": True}
