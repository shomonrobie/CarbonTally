"""Invitations repository (V3 Phase 6).

Persistence for the RC2 ``user_invitations`` table — organisation-scoped
invitation records (email, token, status, expiry). ``role_id`` is a nullable FK
to ``roles``; the customer role set (owner/admin/member/viewer) is the
``organization_members.role`` CHECK model, so when a matching ``roles`` row name
exists it is linked, otherwise ``role_id`` stays NULL and the invitation is
still recorded truthfully (the email/token/status/expiry are real columns).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

_INVITATION_COLUMNS = (
    "id, email, role_id, organization_id, invited_by, token, status, "
    "expires_at, created_at, updated_at"
)


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _row_to_invitation(row: Any) -> dict:
    r = dict(row)
    return {
        "id": str(r["id"]),
        "email": str(r["email"]),
        "role_id": str(r["role_id"]) if r.get("role_id") else None,
        "organization_id": str(r["organization_id"]),
        "invited_by": str(r["invited_by"]) if r.get("invited_by") else None,
        "status": str(r.get("status") or "pending"),
        "expires_at": _iso(r.get("expires_at")),
        "created_at": _iso(r.get("created_at")),
        "updated_at": _iso(r.get("updated_at")),
    }


class InvitationsRepository(AbstractRepository[dict]):
    """CRUD for ``user_invitations`` (org-scoped invitation records)."""

    async def create(
        self,
        org_id: str,
        email: str,
        *,
        token: str,
        role_id: Optional[str] = None,
        invited_by: Optional[str] = None,
        status: str = "pending",
        expires_at: Any = None,
    ) -> dict:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.user_invitations (
                email, role_id, organization_id, invited_by, token, status,
                expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING {_INVITATION_COLUMNS}
            """,
            email,
            role_id,
            org_id,
            invited_by,
            token,
            status,
            expires_at,
        )
        if row is None:
            raise RuntimeError("user_invitations insert returned no row")
        return _row_to_invitation(row)

    async def get(self, invitation_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_INVITATION_COLUMNS} FROM public.user_invitations WHERE id = $1",
            invitation_id,
        )
        return _row_to_invitation(row) if row is not None else None

    async def list_for_org(self, org_id: str) -> list[dict]:
        rows = await self._fetch_all(
            f"""
            SELECT {_INVITATION_COLUMNS} FROM public.user_invitations
            WHERE organization_id = $1
            ORDER BY created_at DESC, id
            """,
            org_id,
        )
        return [_row_to_invitation(r) for r in rows]

    async def revoke(self, invitation_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"""
            UPDATE public.user_invitations
            SET status = 'revoked', updated_at = NOW()
            WHERE id = $1
            RETURNING {_INVITATION_COLUMNS}
            """,
            invitation_id,
        )
        return _row_to_invitation(row) if row is not None else None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        await self._execute(
            "DELETE FROM public.user_invitations WHERE id = $1", id
        )
