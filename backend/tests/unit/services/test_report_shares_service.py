"""CT-IMPLEMENT-03 (PD-1) — canonical report-sharing service tests.

The share contract is the schema's: version-bound, immutable-version-only,
recipient-explicit, permission-checked, expiring, revocable, access-history
bearing, one live share per (version, recipient). These tests assert the service
enforces it and audits it — and that it never invents a policy the schema does not
state (for example sharing a draft, or skipping a duplicate grant silently).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from asyncpg.exceptions import UniqueViolationError

from services.report_shares import (
    AUDIT_SHARE_CREATED,
    AUDIT_SHARE_REVOKED,
    ENTITY_SHARE,
    ReportShareService,
    ShareConflictError,
    ShareNotShareableError,
    ShareValidationError,
)

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


class FakeShares:
    """In-memory ``report_shares`` + ``report_share_access_events``."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.events: list[dict] = []
        self.duplicate = False

    async def create(
        self,
        *,
        organization_id,
        report_id,
        report_version_id,
        permission="view",
        recipient_user_id=None,
        recipient_email=None,
        created_by,
        expires_at=None,
        share_token_hash=None,
    ):
        if self.duplicate:
            raise UniqueViolationError(
                'duplicate key value violates unique constraint '
                '"report_shares_active_recipient_key"'
            )
        row = {
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "report_id": report_id,
            "report_version_id": report_version_id,
            "permission": permission,
            "recipient_user_id": recipient_user_id,
            "recipient_email": recipient_email,
            "created_by": created_by,
            "created_at": NOW,
            "updated_at": NOW,
            "expires_at": expires_at,
            "revoked_at": None,
            "revoked_by": None,
            "revocation_reason": None,
            "access_count": 0,
            "last_accessed_at": None,
            "is_active": True,
        }
        self.rows.append(row)
        return row

    async def get(self, id):
        return next((r for r in self.rows if r["id"] == id), None)

    async def get_for_org(self, id, organization_id):
        row = await self.get(id)
        if row is None or row["organization_id"] != organization_id:
            return None
        return row

    async def list_for_report(self, report_id, *, include_revoked=True, limit=100):
        return [
            r
            for r in self.rows
            if r["report_id"] == report_id and (include_revoked or r["revoked_at"] is None)
        ][:limit]

    async def list_received(
        self,
        *,
        recipient_user_id,
        recipient_email=None,
        include_revoked=False,
        include_expired=False,
        limit=100,
        now=None,
    ):
        matches = []
        for row in self.rows:
            if row["recipient_user_id"] != recipient_user_id and not (
                row["recipient_email"]
                and recipient_email
                and row["recipient_email"] == recipient_email
            ):
                continue
            if not include_revoked and row["revoked_at"] is not None:
                continue
            if not include_expired and row["expires_at"] is not None and row["expires_at"] <= now:
                continue
            matches.append(row)
        return matches[:limit]

    async def revoke(self, share_id, *, revoked_by, reason):
        row = await self.get(share_id)
        if row is None:
            return None
        if row["revoked_at"] is None:
            row.update(
                revoked_at=NOW,
                revoked_by=revoked_by,
                revocation_reason=reason,
                is_active=False,
            )
        return row

    async def record_event(
        self,
        *,
        share_id,
        organization_id,
        report_version_id,
        actor_user_id,
        event_type,
        detail=None,
    ):
        event = {
            "id": str(uuid.uuid4()),
            "share_id": share_id,
            "organization_id": organization_id,
            "report_version_id": report_version_id,
            "actor_user_id": actor_user_id,
            "event_type": event_type,
            "occurred_at": NOW,
            "detail": detail,
        }
        self.events.append(event)
        return event

    async def list_events(self, share_id, *, limit=100):
        return [e for e in self.events if e["share_id"] == share_id][:limit]


class FakeReports:
    def __init__(self, report):
        self._report = report

    async def get_full(self, report_id):
        if self._report is None or self._report["id"] != report_id:
            return None
        return self._report


class FakeVersions:
    def __init__(self, *, current=None, by_number=None):
        self._current = current
        self._by_number = by_number or {}

    async def get_current(self, report_id):
        return self._current

    async def get_by_number(self, report_id, version_number):
        return self._by_number.get(int(version_number))


class FakeAudit:
    def __init__(self) -> None:
        self.entries: list = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry


def make_service(*, status="APPROVED", report_org="org-1", current=None):
    report_id = str(uuid.uuid4())
    report = {"id": report_id, "organization_id": report_org}
    version = current or {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "version_number": 2,
        "status": status,
    }
    shares, audit = FakeShares(), FakeAudit()
    repos = SimpleNamespace(
        report_shares=shares,
        reports=FakeReports(report),
        report_versions=FakeVersions(current=version),
        audit=audit,
    )
    service = ReportShareService(repos, clock=lambda: NOW)
    return service, shares, audit, report_id, version


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------
async def test_share_binds_to_the_current_immutable_version_and_audits():
    service, shares, audit, report_id, version = make_service()

    created = await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["Reader@Example.com"],
    )

    assert len(created) == 1
    row = created[0]
    assert row["report_version_id"] == version["id"]
    assert row["organization_id"] == "org-1"
    assert row["report_id"] == report_id
    assert row["permission"] == "view"
    assert row["created_by"] == "user-1"
    assert row["recipient_email"] == "reader@example.com"
    assert row["recipient_user_id"] is None
    assert row["is_active"] is True
    # one 'created' event and one audit entry, both tied to the artefact
    assert shares.events[0]["event_type"] == "created"
    assert shares.events[0]["detail"]["version_number"] == 2
    assert audit.entries[0].action == AUDIT_SHARE_CREATED
    assert audit.entries[0].correlation_id == report_id
    assert audit.entries[0].entity_type == ENTITY_SHARE
    assert audit.entries[0].entity_id == row["id"]


@pytest.mark.parametrize("status", ["DRAFT", "REVIEWED", "CHANGES_REQUESTED", "REJECTED"])
async def test_share_refuses_a_version_that_is_not_immutable(status):
    service, shares, audit, report_id, _ = make_service(status=status)

    with pytest.raises(ShareNotShareableError) as excinfo:
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )

    assert status in str(excinfo.value)
    assert shares.rows == [] and shares.events == [] and audit.entries == []


async def test_share_accepts_a_final_version_too():
    service, _, _, report_id, version = make_service(status="FINAL")
    created = await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["reader@example.com"],
    )
    assert created[0]["report_version_id"] == version["id"]


async def test_share_honours_an_explicit_version_number():
    service, _, _, report_id, _ = make_service()
    explicit = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "version_number": 1,
        "status": "FINAL",
    }
    service._repos.report_versions._by_number = {1: explicit}

    created = await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["reader@example.com"],
        version_number=1,
    )
    assert created[0]["report_version_id"] == explicit["id"]


async def test_share_refuses_an_unknown_version_or_report():
    service, shares, _, report_id, _ = make_service()
    with pytest.raises(ShareValidationError):
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["r@example.com"],
            version_number=99,
        )
    with pytest.raises(ShareValidationError):
        await service.share(
            organization_id="org-2",  # report belongs to org-1
            report_id=report_id,
            actor="user-1",
            recipients=["r@example.com"],
        )
    assert shares.rows == []


async def test_share_refuses_an_invalid_permission_expiry_or_empty_recipients():
    service, shares, _, report_id, _ = make_service()
    for kwargs in (
        {"permission": "edit"},
        {"expires_at": NOW - timedelta(days=1)},
        {"expires_at": datetime(2026, 6, 1, 12, 0)},  # naive
        {"recipients": []},
        {"recipients": ["   "]},
    ):
        payload = {"recipients": ["r@example.com"], "permission": "view"}
        payload.update(kwargs)
        with pytest.raises(ShareValidationError):
            await service.share(
                organization_id="org-1",
                report_id=report_id,
                actor="user-1",
                **payload,
            )
    assert shares.rows == []


async def test_share_surfaces_a_duplicate_live_grant_as_a_conflict():
    service, shares, _, report_id, _ = make_service()
    shares.duplicate = True

    with pytest.raises(ShareConflictError) as excinfo:
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )
    assert "revoke" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Revocation
# ---------------------------------------------------------------------------
async def test_revoke_requires_a_reason_and_is_self_describing():
    service, shares, audit, report_id, _ = make_service()
    share = (
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )
    )[0]

    with pytest.raises(ShareValidationError):
        await service.revoke(
            org_scope="org-1", share_id=share["id"], actor="user-1", reason="  "
        )

    revoked = await service.revoke(
        org_scope="org-1",
        share_id=share["id"],
        actor="user-1",
        reason="Recipient changed role",
    )

    assert revoked["revoked_at"] is not None
    assert revoked["revoked_by"] == "user-1"
    assert revoked["revocation_reason"] == "Recipient changed role"
    assert revoked["is_active"] is False
    assert shares.events[-1]["event_type"] == "revoked"
    assert shares.events[-1]["detail"] == {"reason": "Recipient changed role"}
    assert [e.action for e in audit.entries] == [AUDIT_SHARE_CREATED, AUDIT_SHARE_REVOKED]
    assert audit.entries[-1].correlation_id == report_id


async def test_revoke_is_one_way_and_scoped_to_the_organisation():
    service, shares, audit, report_id, _ = make_service()
    share = (
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )
    )[0]

    assert await service.revoke(
        org_scope="org-2", share_id=share["id"], actor="user-1", reason="nope"
    ) is None
    assert share["revoked_at"] is None, "another tenant cannot revoke this share"

    await service.revoke(
        org_scope="org-1", share_id=share["id"], actor="user-1", reason="first reason"
    )
    again = await service.revoke(
        org_scope="org-1", share_id=share["id"], actor="user-2", reason="second"
    )

    assert again["revocation_reason"] == "first reason", "the first revocation wins"
    assert again["revoked_by"] == "user-1"
    assert [e["event_type"] for e in shares.events].count("revoked") == 1
    assert [e.action for e in audit.entries].count(AUDIT_SHARE_REVOKED) == 1


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
async def test_received_returns_live_unexpired_shares_addressed_to_the_caller():
    service, shares, _, report_id, _ = make_service()
    await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["reader@example.com"],
    )
    live = await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["other@example.com"],
    )
    await service.revoke(
        org_scope="org-1", share_id=live[0]["id"], actor="user-1", reason="done"
    )

    received = await service.received(user_id="someone-else", email="reader@example.com")
    assert [row["recipient_email"] for row in received] == ["reader@example.com"]

    assert await service.received(user_id="nobody", email="nobody@example.com") == []


async def test_received_excludes_expired_shares():
    service, _, _, report_id, _ = make_service()
    await service.share(
        organization_id="org-1",
        report_id=report_id,
        actor="user-1",
        recipients=["reader@example.com"],
        expires_at=NOW + timedelta(days=1),
    )
    service._repos.report_shares.rows[0]["expires_at"] = NOW - timedelta(minutes=1)

    assert await service.received(user_id="x", email="reader@example.com") == []


async def test_access_history_is_append_only_and_none_for_an_unknown_share():
    service, shares, _, report_id, _ = make_service()
    share = (
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )
    )[0]

    history = await service.access_history(share["id"])
    assert [e["event_type"] for e in history] == ["created"]
    assert await service.access_history(str(uuid.uuid4())) is None

    listed = await service.list_for_report(report_id)
    assert [row["id"] for row in listed] == [share["id"]]
    assert shares.rows[0]["access_count"] == 0


async def test_share_rows_are_shaped_for_json_without_raw_database_types():
    from services.report_shares import shape_event, shape_share

    service, _, _, report_id, _ = make_service()
    share = (
        await service.share(
            organization_id="org-1",
            report_id=report_id,
            actor="user-1",
            recipients=["reader@example.com"],
        )
    )[0]

    shaped = shape_share(share)
    assert shaped["created_at"] == NOW.isoformat()
    assert shaped["is_active"] is True
    assert shaped["recipient_email"] == "reader@example.com"

    event = shape_event(service._repos.report_shares.events[0])
    assert event["occurred_at"] == NOW.isoformat()
    assert event["event_type"] == "created"
