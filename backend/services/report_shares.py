"""Canonical report-sharing service (CT-IMPLEMENT-03 / PD-1).

The application layer for PD-1 sharing: validation, version binding, recipient
resolution and auditing, on top of ``data.report_shares``.

What the canonical model decides (and therefore what this service implements —
nothing more):

* a share is bound to **one report version**, and only a version whose lifecycle
  state is immutable (``APPROVED``/``FINAL``) may be shared;
* a share names an explicit recipient (a user id and/or an email address);
* the permission is ``view`` or ``download``;
* a share may expire, and expiry is evaluated server-side;
* a share is **revoked**, never erased — revocation is a self-describing update
  (actor + reason) and the register keeps the history;
* one live share per (version, recipient): re-sharing means revoke-then-share,
  so a recipient cannot accumulate ambiguous duplicate grants.

Consuming a share (returning the report content to the recipient, recording
``access``/``download``/``denied`` events) is deliberately **not** implemented
here — see the CT-IMPLEMENT-03 report, PO-gated item G-2. The schema's event
vocabulary already carries those event types; no delivery policy has been
invented in their place.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from asyncpg.exceptions import UniqueViolationError

from core.logging import get_logger
from data.report_shares import (
    EVENT_CREATED,
    EVENT_REVOKED,
    PERMISSIONS,
    ReportSharesRepository,
)
from domain.audit import (
    ACTOR_ORG_USER,
    CAT_REPORT,
    ORIGIN_HUMAN,
    OUTCOME_FAILURE,
    OUTCOME_SUCCESS,
    AuditEntry,
)
from domain.report_lifecycle import IMMUTABLE_STATUSES, is_immutable

logger = get_logger(__name__)

#: Audit actions for the share register (all classify to CAT_REPORT).
AUDIT_SHARE_CREATED = "report_share_created"
AUDIT_SHARE_REVOKED = "report_share_revoked"

#: Entity name recorded on share audit entries.
ENTITY_SHARE = "report_shares"


class ShareValidationError(ValueError):
    """A share request the canonical model (and the schema) rejects."""

    def __init__(self, message: str, *, field: Optional[str] = None) -> None:
        super().__init__(message)
        self.field = field


class ShareNotShareableError(ShareValidationError):
    """The addressed version is not an immutable (APPROVED/FINAL) version."""


class ShareConflictError(ValueError):
    """The request conflicts with an existing live share."""


def validate_permission(permission: object) -> str:
    """Return the share permission, else raise (mirrors the permission CHECK)."""
    if not isinstance(permission, str) or permission not in PERMISSIONS:
        raise ShareValidationError(
            f"unsupported share permission {permission!r}; canonical permissions are "
            f"{', '.join(PERMISSIONS)}",
            field="permission",
        )
    return permission


def normalise_recipient(value: Any) -> dict[str, Optional[str]]:
    """Normalise one recipient into ``{"user_id": …, "email": …}``.

    A value containing ``@`` is an email address and is lower-cased (the schema's
    ``report_shares_email_normalised_check`` requires the stored form to be lower
    case); anything else is a user id. At least one of the two is always
    populated, so the schema's "recipient is explicit" requirement cannot be
    satisfied by an empty value.
    """
    if isinstance(value, Mapping):
        user_id = value.get("user_id") or None
        email = value.get("email") or None
        if not user_id and not email:
            raise ShareValidationError(
                "a share recipient must name a user id or an email address",
                field="recipients",
            )
        return {
            "user_id": str(user_id) if user_id else None,
            "email": str(email).lower() if email else None,
        }
    text = str(value or "").strip()
    if not text:
        raise ShareValidationError(
            "a share recipient must name a user id or an email address",
            field="recipients",
        )
    if "@" in text:
        return {"user_id": None, "email": text.lower()}
    return {"user_id": text, "email": None}


def normalise_recipients(values: Sequence[Any]) -> list[dict[str, Optional[str]]]:
    """Normalise a recipient list, refusing an empty one."""
    if not values:
        raise ShareValidationError(
            "a share requires at least one recipient", field="recipients"
        )
    return [normalise_recipient(value) for value in values]


def validate_expiry(
    expires_at: Optional[datetime], *, now: datetime
) -> Optional[datetime]:
    """Return an expiry that is genuinely in the future, else raise.

    The schema only requires ``expires_at > created_at``; a share created with an
    expiry already in the past would be born dead, which is a request error rather
    than a valid state, so it is refused here with an explanation.
    """
    if expires_at is None:
        return None
    if expires_at.tzinfo is None:
        raise ShareValidationError(
            "expires_at must include a timezone", field="expires_at"
        )
    if expires_at <= now:
        raise ShareValidationError(
            "expires_at must be in the future", field="expires_at"
        )
    return expires_at


def _iso(value: Any) -> Any:
    """ISO-8601 for datetime columns, verbatim for anything else."""
    return value.isoformat() if getattr(value, "isoformat", None) else value


def shape_share(row: Mapping[str, Any]) -> dict:
    """JSON-ready shape of one share row (no raw database types)."""
    return {
        "id": str(row["id"]),
        "organization_id": str(row["organization_id"]),
        "report_id": str(row["report_id"]),
        "report_version_id": str(row["report_version_id"]),
        "permission": row.get("permission"),
        "recipient_user_id": row.get("recipient_user_id"),
        "recipient_email": row.get("recipient_email"),
        "created_by": row.get("created_by"),
        "created_at": _iso(row.get("created_at")),
        "expires_at": _iso(row.get("expires_at")),
        "revoked_at": _iso(row.get("revoked_at")),
        "revoked_by": row.get("revoked_by"),
        "revocation_reason": row.get("revocation_reason"),
        "access_count": int(row.get("access_count") or 0),
        "last_accessed_at": _iso(row.get("last_accessed_at")),
        "is_active": bool(row.get("is_active", row.get("revoked_at") is None)),
    }


def shape_event(row: Mapping[str, Any]) -> dict:
    """JSON-ready shape of one share access-history entry."""
    return {
        "id": str(row["id"]),
        "share_id": str(row["share_id"]),
        "report_version_id": str(row["report_version_id"]),
        "actor_user_id": row.get("actor_user_id"),
        "event_type": row.get("event_type"),
        "occurred_at": _iso(row.get("occurred_at")),
        "detail": row.get("detail"),
    }


class ReportShareService:
    """Canonical create/read/revoke/access-history for report shares.

    Args:
        repos: The request repository bundle (``report_shares``,
            ``report_versions``, ``reports`` and the ``audit`` sink).
        clock: Optional aware-time source (injectable so expiry checks and audit
            timestamps are deterministic in tests).
    """

    def __init__(self, repos: Any, *, clock: Optional[Any] = None) -> None:
        self._repos = repos
        self._shares: ReportSharesRepository = repos.report_shares
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def list_for_report(
        self, report_id: str, *, include_revoked: bool = True
    ) -> list[dict]:
        """The share register of one report (live grants and revoked history)."""
        return await self._shares.list_for_report(
            report_id, include_revoked=include_revoked
        )

    async def access_history(
        self, share_id: str, *, limit: int = 100
    ) -> Optional[list[dict]]:
        """Append-only access/revocation history of one share, or ``None``."""
        share = await self._shares.get(share_id)
        if share is None:
            return None
        return await self._shares.list_events(share_id, limit=limit)

    async def received(self, *, user_id: str, email: Optional[str]) -> list[dict]:
        """Shares addressed to the calling recipient (unrevoked, unexpired)."""
        return await self._shares.list_received(
            recipient_user_id=user_id, recipient_email=email, now=self._clock()
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def share(
        self,
        *,
        organization_id: str,
        report_id: str,
        actor: str,
        recipients: Sequence[Any],
        permission: object = "view",
        version_number: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> list[dict]:
        """Share one immutable version of a report with explicit recipients.

        The version is resolved and *proved* immutable before anything is
        written, so an ineligible request is refused with a described 409 rather
        than reaching the schema trigger. When ``version_number`` is omitted the
        report's current version is used — PD-1 sharing is version-bound, so
        "share this report" can only ever mean "share its current version".

        Returns the created share rows (one per recipient).
        """
        now = self._clock()
        validated_permission = validate_permission(permission)
        validated_recipients = normalise_recipients(recipients)
        validated_expiry = validate_expiry(expires_at, now=now)

        report = await self._repos.reports.get_full(report_id)
        if report is None or str(report["organization_id"]) != str(organization_id):
            raise ShareValidationError(
                "report not found in this organisation", field="report_id"
            )
        version = await self._resolve_version(report_id, version_number)
        status = str(version.get("status") or "")
        if not is_immutable(status):
            raise ShareNotShareableError(
                f"report version {version['version_number']} is in state {status} — "
                f"only an immutable version ({'/'.join(IMMUTABLE_STATUSES)}) may be "
                f"shared; approve or finalize it first",
                field="version_number",
            )

        created: list[dict] = []
        for recipient in validated_recipients:
            try:
                row = await self._shares.create(
                    organization_id=organization_id,
                    report_id=report_id,
                    report_version_id=str(version["id"]),
                    permission=validated_permission,
                    recipient_user_id=recipient["user_id"],
                    recipient_email=recipient["email"],
                    created_by=actor,
                    expires_at=validated_expiry,
                )
            except UniqueViolationError as exc:
                raise ShareConflictError(
                    "that recipient already holds a live share of this version; "
                    "revoke it before sharing again"
                ) from exc
            await self._shares.record_event(
                share_id=row["id"],
                organization_id=organization_id,
                report_version_id=str(version["id"]),
                actor_user_id=actor,
                event_type=EVENT_CREATED,
                detail={
                    "permission": validated_permission,
                    "recipient_user_id": recipient["user_id"],
                    "recipient_email": recipient["email"],
                    "version_number": version["version_number"],
                },
            )
            await self._audit(
                AUDIT_SHARE_CREATED,
                organization_id=organization_id,
                report_id=report_id,
                share_id=row["id"],
                actor=actor,
                after={
                    "permission": validated_permission,
                    "recipient_user_id": recipient["user_id"],
                    "recipient_email": recipient["email"],
                    "version_number": version["version_number"],
                    "expires_at": _iso(validated_expiry),
                },
            )
            created.append(row)
        return created

    async def revoke(
        self, *, org_scope: str, share_id: str, actor: str, reason: object
    ) -> Optional[dict]:
        """Revoke one share, self-describingly (actor + reason + time).

        ``org_scope`` is the organisation the caller is authorized for: a share
        outside it resolves to ``None`` (404), never to a row the caller is then
        trusted to filter. A reason is mandatory because the schema requires the
        revocation to be self-describing.
        """
        text = str(reason or "").strip()
        if not text:
            raise ShareValidationError("a revocation reason is required", field="reason")
        share = await self._shares.get_for_org(share_id, org_scope)
        if share is None:
            return None
        if share.get("revoked_at") is not None:
            # Already revoked. Nothing changes and nothing is re-audited: the
            # original actor and reason stay on the record.
            return share
        row = await self._shares.revoke(share_id, revoked_by=actor, reason=text)
        if row is None:
            return None
        await self._shares.record_event(
            share_id=share_id,
            organization_id=str(row["organization_id"]),
            report_version_id=str(row["report_version_id"]),
            actor_user_id=actor,
            event_type=EVENT_REVOKED,
            detail={"reason": text},
        )
        await self._audit(
            AUDIT_SHARE_REVOKED,
            organization_id=str(row["organization_id"]),
            report_id=str(row["report_id"]),
            share_id=share_id,
            actor=actor,
            before={"is_active": True},
            after={"is_active": False, "revocation_reason": text},
        )
        return row

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _resolve_version(
        self, report_id: str, version_number: Optional[int]
    ) -> dict:
        """Return the addressed version, or the report's current version."""
        if version_number is None:
            current = await self._repos.report_versions.get_current(report_id)
            if current is None:
                raise ShareValidationError(
                    "this report has no version to share yet; generate it first",
                    field="report_id",
                )
            return current
        version = await self._repos.report_versions.get_by_number(
            report_id, int(version_number)
        )
        if version is None:
            raise ShareValidationError(
                f"report has no version {version_number}", field="version_number"
            )
        return version

    async def _audit(
        self,
        action: str,
        *,
        organization_id: str,
        report_id: str,
        share_id: str,
        actor: str,
        before: Optional[Mapping[str, Any]] = None,
        after: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Append one share event to the canonical audit trail.

        ``correlation_id`` is the **report** id, so a report's share events sit
        alongside its lifecycle events in the same chain. Only the share id and
        field states are stored — never a token, a signed URL or report content.
        Best-effort: an audit failure is logged and never breaks the change.
        """
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=report_id,
            entity_type=ENTITY_SHARE,
            entity_id=share_id,
            action=action,
            actor=actor,
            occurred_at=self._clock(),
            changed_fields={"report_id": report_id, "share_id": share_id},
            reason=f"report share {action}",
            before=dict(before) if before else None,
            after=dict(after) if after else None,
            actor_type=ACTOR_ORG_USER,
            origin=ORIGIN_HUMAN,
            outcome=OUTCOME_SUCCESS,
            organization_id=organization_id,
            # The actor is a member of the organisation that owns the share.
            actor_organization_id=organization_id,
            category=CAT_REPORT,
        )
        try:
            await self._repos.audit.record(entry)
        except Exception:  # noqa: BLE001 — audit must never break the operation
            logger.exception("report share audit (%s) failed for %s", action, share_id)
