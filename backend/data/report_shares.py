"""Canonical report-sharing repository (CT-IMPLEMENT-03 / PD-1).

Persistence for the CT-IMPLEMENT-02 canonical share tables —
``report_shares`` (one share of one **immutable** report version) and
``report_share_access_events`` (append-only access/revocation history).

It is **not** the retired ``report_history`` table, and no share is ever stored
in a JSONB ``metadata`` blob (which is how the legacy route did it, and why
sharing had no server-side authorization, no tenant isolation, no expiry and no
revocation).

The schema is the authority for the share contract; this module only writes what
the schema accepts:

* ``ct02_report_share_validate`` refuses a share whose version is absent, belongs
  to another tenant, or is not ``APPROVED``/``FINAL``;
* ``ct02_report_share_update_guard`` freezes identity/scope, so revocation is a
  one-way update of the revocation columns only;
* ``report_shares_active_recipient_key`` allows one live share per
  (version, recipient) — re-sharing is revoke-then-create, never a duplicate;
* ``report_share_access_events`` accepts no UPDATE, DELETE or TRUNCATE.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb

#: Every column of ``report_shares`` this application uses.
_SHARE_COLUMNS = """
    id, organization_id, report_id, report_version_id, permission,
    recipient_user_id, recipient_email, created_by, created_at, updated_at,
    expires_at, revoked_at, revoked_by, revocation_reason, access_count,
    last_accessed_at
"""

#: Every column of ``report_share_access_events`` this application uses.
_EVENT_COLUMNS = """
    id, share_id, organization_id, report_version_id, actor_user_id,
    event_type, occurred_at, detail
"""

#: The share-scoped event vocabulary the schema's CHECK accepts.
EVENT_CREATED = "created"
EVENT_ACCESS = "access"
EVENT_DOWNLOAD = "download"
EVENT_REVOKED = "revoked"
EVENT_DENIED = "denied"
EVENT_TYPES: tuple[str, ...] = (
    EVENT_CREATED,
    EVENT_ACCESS,
    EVENT_DOWNLOAD,
    EVENT_REVOKED,
    EVENT_DENIED,
)

#: The share permission vocabulary the schema's CHECK accepts.
PERMISSIONS: tuple[str, ...] = ("view", "download")


def _row_to_share(row: Any) -> dict:
    """Map one share row to its canonical dict form."""
    r = dict(row)
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "report_id": str(r["report_id"]),
        "report_version_id": str(r["report_version_id"]),
        "permission": str(r["permission"]),
        "recipient_user_id": (
            str(r["recipient_user_id"]) if r.get("recipient_user_id") else None
        ),
        "recipient_email": r.get("recipient_email"),
        "created_by": str(r["created_by"]) if r.get("created_by") else None,
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
        "expires_at": r.get("expires_at"),
        "revoked_at": r.get("revoked_at"),
        "revoked_by": str(r["revoked_by"]) if r.get("revoked_by") else None,
        "revocation_reason": r.get("revocation_reason"),
        "access_count": int(r.get("access_count") or 0),
        "last_accessed_at": r.get("last_accessed_at"),
        "is_active": r.get("revoked_at") is None,
    }


def _row_to_event(row: Any) -> dict:
    """Map one access-event row to its canonical dict form (JSONB decoded)."""
    r = dict(row)
    return {
        "id": str(r["id"]),
        "share_id": str(r["share_id"]),
        "organization_id": str(r["organization_id"]),
        "report_version_id": str(r["report_version_id"]),
        "actor_user_id": str(r["actor_user_id"]) if r.get("actor_user_id") else None,
        "event_type": str(r["event_type"]),
        "occurred_at": r.get("occurred_at"),
        "detail": loads_jsonb(r.get("detail")),
    }


class ReportSharesRepository(AbstractRepository[dict]):
    """Persistence for ``report_shares`` / ``report_share_access_events``."""

    async def create(
        self,
        *,
        organization_id: str,
        report_id: str,
        report_version_id: str,
        permission: str = "view",
        recipient_user_id: Optional[str] = None,
        recipient_email: Optional[str] = None,
        created_by: str,
        expires_at: Optional[datetime] = None,
        share_token_hash: Optional[str] = None,
    ) -> dict:
        """Insert one share of one immutable report version.

        The version/organisation/state invariants are enforced by the schema
        trigger, not re-implemented here: an insert that violates them raises the
        database's own ``check_violation`` / ``insufficient_privilege`` /
        ``foreign_key_violation``, which the service layer surfaces as a client
        error rather than as a 500.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_shares (
                organization_id, report_id, report_version_id, permission,
                recipient_user_id, recipient_email, created_by, expires_at,
                share_token_hash
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4,
                $5::uuid, $6, $7::uuid, $8, $9
            )
            RETURNING {_SHARE_COLUMNS}
            """,
            organization_id,
            report_id,
            report_version_id,
            permission,
            recipient_user_id,
            recipient_email,
            created_by,
            expires_at,
            share_token_hash,
        )
        if row is None:
            raise RuntimeError("report share insert returned no row")
        return _row_to_share(row)

    async def get(self, id: str) -> Optional[dict]:
        """Return one share, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_SHARE_COLUMNS} FROM public.report_shares WHERE id = $1::uuid",
            id,
        )
        return _row_to_share(row) if row is not None else None

    async def get_for_org(self, id: str, organization_id: str) -> Optional[dict]:
        """Return one share **scoped to its owning organisation**, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_SHARE_COLUMNS} FROM public.report_shares "
            "WHERE id = $1::uuid AND organization_id = $2::uuid",
            id,
            organization_id,
        )
        return _row_to_share(row) if row is not None else None

    async def list_for_report(
        self, report_id: str, *, include_revoked: bool = True, limit: int = 100
    ) -> list[dict]:
        """Every share of a report, newest first.

        Revoked shares are returned by default: the share register is history
        (a share is revoked, never erased), and a caller that only wants live
        grants filters on ``is_active``.
        """
        clause = "" if include_revoked else " AND revoked_at IS NULL"
        rows = await self._fetch_all(
            f"""
            SELECT {_SHARE_COLUMNS} FROM public.report_shares
             WHERE report_id = $1::uuid{clause}
             ORDER BY created_at DESC, id
             LIMIT $2
            """,
            report_id,
            int(limit),
        )
        return [_row_to_share(r) for r in rows]

    async def list_received(
        self,
        *,
        recipient_user_id: str,
        recipient_email: Optional[str] = None,
        include_revoked: bool = False,
        include_expired: bool = False,
        limit: int = 100,
        now: Optional[datetime] = None,
    ) -> list[dict]:
        """Shares addressed to the calling recipient (user id and/or email).

        This mirrors the schema's own read predicate for a recipient
        (``recipient_user_id = auth.uid()`` or a case-insensitive email match),
        so the application cannot see a different set from the one RLS allows.
        """
        args: list[Any] = [recipient_user_id, (recipient_email or "").lower()]
        predicates = [
            "(recipient_user_id = $1::uuid"
            " OR (recipient_email IS NOT NULL AND lower(recipient_email) = $2))"
        ]
        if not include_revoked:
            predicates.append("revoked_at IS NULL")
        if not include_expired:
            args.append(now)
            predicates.append(f"(expires_at IS NULL OR expires_at > ${len(args)})")
        args.append(int(limit))
        rows = await self._fetch_all(
            f"""
            SELECT {_SHARE_COLUMNS} FROM public.report_shares
             WHERE {' AND '.join(predicates)}
             ORDER BY created_at DESC, id
             LIMIT ${len(args)}
            """,
            *args,
        )
        return [_row_to_share(r) for r in rows]

    async def revoke(
        self,
        share_id: str,
        *,
        revoked_by: str,
        reason: str,
    ) -> Optional[dict]:
        """Revoke a share once; ``None`` when it does not exist.

        Only the revocation bookkeeping columns change (the schema's update guard
        permits exactly those), and the ``revoked_at IS NULL`` predicate makes a
        second revocation a no-op rather than a rewrite of the first — the
        original reason and actor are preserved. The stored state is returned
        either way, so the caller can distinguish "already revoked" from
        "not found".
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.report_shares
               SET revoked_at = NOW(),
                   revoked_by = $2::uuid,
                   revocation_reason = $3,
                   updated_at = NOW()
             WHERE id = $1::uuid AND revoked_at IS NULL
            RETURNING {_SHARE_COLUMNS}
            """,
            share_id,
            revoked_by,
            reason,
        )
        if row is not None:
            return _row_to_share(row)
        return await self.get(share_id)

    async def record_event(
        self,
        *,
        share_id: str,
        organization_id: str,
        report_version_id: str,
        actor_user_id: Optional[str],
        event_type: str,
        detail: Optional[Any] = None,
    ) -> dict:
        """Append one access/revocation event (append-only by construction).

        ``detail`` must never carry tokens, signed URLs or credentials
        (AGENTS.md §68 / the schema's own comment); callers pass identifiers and
        field names only.
        """
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported share event type {event_type!r}")
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_share_access_events (
                share_id, organization_id, report_version_id, actor_user_id,
                event_type, detail
            ) VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6::jsonb)
            RETURNING {_EVENT_COLUMNS}
            """,
            share_id,
            organization_id,
            report_version_id,
            actor_user_id,
            event_type,
            dumps_jsonb(detail) if detail is not None else None,
        )
        if row is None:
            raise RuntimeError("report share access-event insert returned no row")
        return _row_to_event(row)

    async def list_events(self, share_id: str, *, limit: int = 100) -> list[dict]:
        """Access history for one share, newest first."""
        rows = await self._fetch_all(
            f"""
            SELECT {_EVENT_COLUMNS} FROM public.report_share_access_events
             WHERE share_id = $1::uuid
             ORDER BY occurred_at DESC, id
             LIMIT $2
            """,
            share_id,
            int(limit),
        )
        return [_row_to_event(r) for r in rows]

    # ------------------------------------------------------------------
    # AbstractRepository contract
    # ------------------------------------------------------------------
    async def save(self, entity: dict) -> dict:
        """Unused: a share is created once and then revoked; never re-saved."""
        raise NotImplementedError(
            "use ReportSharesRepository.create/revoke for share writes"
        )

    async def delete(self, id: str) -> None:
        """Refused by design: a share is revoked, never erased (PD-1)."""
        raise NotImplementedError(
            "a report share is revoked (ReportSharesRepository.revoke), never deleted"
        )
