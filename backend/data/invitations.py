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
    "expires_at, created_at, updated_at, role, invited_by_firm_id, "
    "accepted_at, accepted_by, revoked_at, revoked_by"
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
        # CT04 (PD-1A): the single-use token is returned to the AUTHORISED
        # org-admin / consultant that created or lists the invitation so the
        # accept link can be issued. The API surfaces are admin-gated; the token
        # is never exposed to a non-privileged caller.
        "token": str(r["token"]) if r.get("token") else None,
        "status": str(r.get("status") or "pending"),
        "expires_at": _iso(r.get("expires_at")),
        "created_at": _iso(r.get("created_at")),
        "updated_at": _iso(r.get("updated_at")),
        # CT04 (PD-1A/PD-2A) additive columns — use .get so memory/test rows and
        # pre-CT04 rows (which lack them) degrade gracefully rather than KeyError.
        "role": (str(r["role"]) if r.get("role") else None),
        "invited_by_firm_id": (
            str(r["invited_by_firm_id"]) if r.get("invited_by_firm_id") else None
        ),
        "accepted_at": _iso(r.get("accepted_at")),
        "accepted_by": str(r["accepted_by"]) if r.get("accepted_by") else None,
        "revoked_at": _iso(r.get("revoked_at")),
        "revoked_by": str(r["revoked_by"]) if r.get("revoked_by") else None,
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
        role: Optional[str] = None,
        invited_by_firm_id: Optional[str] = None,
    ) -> dict:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.user_invitations (
                email, role_id, organization_id, invited_by, token, status,
                expires_at, role, invited_by_firm_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING {_INVITATION_COLUMNS}
            """,
            email,
            role_id,
            org_id,
            invited_by,
            token,
            status,
            expires_at,
            role,
            invited_by_firm_id,
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

    async def get_by_token(self, token: str) -> Optional[dict]:
        """Fetch a single invitation by its (UNIQUE) token, or None."""
        row = await self._fetch_one(
            f"SELECT {_INVITATION_COLUMNS} FROM public.user_invitations WHERE token = $1",
            token,
        )
        return _row_to_invitation(row) if row is not None else None

    async def consume(
        self, token: str, *, accepted_by: Optional[str] = None
    ) -> Optional[dict]:
        """Atomically accept a still-pending, unexpired invitation (PD-1A).

        The conditional ``UPDATE`` is the single-use guarantee: it matches only a
        ``pending`` row whose ``expires_at`` has not passed, so a second
        acceptance (or one via a stale/expired token) matches no row and returns
        ``None``. No read-then-write race exists.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.user_invitations
            SET status = 'accepted', accepted_at = NOW(), accepted_by = $2,
                updated_at = NOW()
            WHERE token = $1
              AND status = 'pending'
              AND (expires_at IS NULL OR expires_at > NOW())
            RETURNING {_INVITATION_COLUMNS}
            """,
            token,
            accepted_by,
        )
        return _row_to_invitation(row) if row is not None else None

    async def revoke(
        self, invitation_id: str, *, revoked_by: Optional[str] = None
    ) -> Optional[dict]:
        row = await self._fetch_one(
            f"""
            UPDATE public.user_invitations
            SET status = 'revoked',
                revoked_at = COALESCE(revoked_at, NOW()),
                revoked_by = COALESCE(revoked_by, $2),
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_INVITATION_COLUMNS}
            """,
            invitation_id,
            revoked_by,
        )
        return _row_to_invitation(row) if row is not None else None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        await self._execute(
            "DELETE FROM public.user_invitations WHERE id = $1", id
        )
