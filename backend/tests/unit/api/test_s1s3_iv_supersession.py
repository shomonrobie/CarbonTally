"""Phase 8 S1/S3 — INDEPENDENT VERIFICATION supersession & denial probes.

Task: ``CT-P8-S1S3-INDEPENDENT-VERIFICATION-20260913-030`` — discharging the
S1/S3 verification asymmetry recorded as finding **F-049-6**.

The implementation suite already covers the basic lifecycle happy path and the
owner/admin vs member/viewer authority split. These probes are the *independent*
pass and cover the ratified rules it does **not** establish end to end:

==========================  =====================================================
Probe                       Ratified rule (Reporting Lifecycle Spec)
==========================  =====================================================
``IV-S3-A1``                §14.1/§18 — supersession creates a **new** ``DRAFT``
                            version, the approved version is never mutated, and
                            the new version does **not** inherit the approval
``IV-S3-A2``                §23.2 — only CHANGES_REQUESTED/REJECTED/APPROVED/FINAL
                            may be superseded; a refused supersession writes nothing
``IV-S3-A3``                §10.2 — Processing Entity staff have no lifecycle
                            authority over a customer report
``IV-S3-A4``                §26.1 — a denied (403) or invalid (409) transition
                            changes no state and emits no audit event
``IV-S3-A5``                §13 — ``APPROVED`` cannot be skipped: finalize from
                            ``DRAFT`` is refused
``IV-S3-A6``                §13 — ``FINAL`` is terminal for every action
``IV-S3-A7``                §14 — history stays readable after supersession
==========================  =====================================================

No database access: the in-memory world mirrors the production repository
contract (including the S1-A demotion rule).
"""
from __future__ import annotations

import asyncio

from domain.report_lifecycle import APPROVED, DRAFT, FINAL, REVIEWED
from tests.unit.api.fakes import entity_operator_user, member_user, org_owner_user

_URL = "/api/v3/reports/{report_id}/versions/{version_number}/{action}"
_CREATE_VERSION = "/api/v3/reports/{report_id}/versions"


def _seed_report(world, report_id: str = "rep-1", org_id: str = "org-a") -> dict:
    return world.reports.seed_report(
        report_id=report_id,
        org_id=org_id,
        status="completed",
        content={
            "page_count": 12,
            "content": {"totals": {"total_co2e_kg": "183.000000"}},
        },
    )


def _seed_version(
    world,
    report_id: str = "rep-1",
    version_number: int = 1,
    status: str = DRAFT,
    is_current: bool = True,
) -> dict:
    return asyncio.run(
        world.report_versions.create(
            report_id,
            version_number=version_number,
            content={"v": version_number},
            is_current=is_current,
            status=status,
        )
    )


def _version(world, report_id: str, version_number: int) -> dict:
    return asyncio.run(world.report_versions.get_by_number(report_id, version_number))


def _current_numbers(world, report_id: str) -> list[int]:
    return [
        v["version_number"]
        for v in asyncio.run(world.report_versions.list_for_report(report_id))
        if v["is_current"]
    ]


def _events(world, action: str) -> list:
    return [e for e in world.audit._entries if e.action == action]


# ---------------------------------------------------------------------------
# Supersession & immutability (§14.1, §18, §23.2)
# ---------------------------------------------------------------------------


def test_iv_s3_a1_supersession_creates_a_new_draft_and_never_mutates_approval(
    client, world, user_provider
) -> None:
    """IV-S3-A1 — the post-approval change path is additive, never in-place."""
    _seed_report(world)
    v1 = _seed_version(world, version_number=1, status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    approved = client.post(_URL.format(report_id="rep-1", version_number=1, action="approve"))
    assert approved.status_code == 200 and approved.json()["status"] == APPROVED

    created = client.post(_CREATE_VERSION.format(report_id="rep-1"), json={"from_version_number": 1})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["version_number"] == 2 and body["status"] == DRAFT
    assert body["is_current"] is True

    # The approved version is exactly as it was: same row, same state, same content.
    after = _version(world, "rep-1", 1)
    assert after["id"] == v1["id"]
    assert after["status"] == APPROVED
    assert after["content"] == {"v": 1}
    assert after["is_current"] is False

    # Exactly one current version, and the approval was not re-issued.
    assert _current_numbers(world, "rep-1") == [2]
    assert len(_events(world, "report.approved")) == 1
    assert _events(world, "report.approved")[0].entity_id == v1["id"]


def test_iv_s3_a2_supersession_from_draft_is_refused_and_writes_nothing(
    client, world, user_provider
) -> None:
    """IV-S3-A2 — only a review-decided/approved/final version may be superseded."""
    _seed_report(world)
    _seed_version(world, version_number=1, status=DRAFT)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    resp = client.post(_CREATE_VERSION.format(report_id="rep-1"), json={"from_version_number": 1})
    assert resp.status_code == 409
    assert len(asyncio.run(world.report_versions.list_for_report("rep-1"))) == 1


def test_iv_s3_a7_history_stays_readable_after_supersession(
    client, world, user_provider
) -> None:
    """IV-S3-A7 — superseded versions remain viewable (§14 "can an old version be viewed")."""
    _seed_report(world)
    _seed_version(world, version_number=1, status=APPROVED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert (
        client.post(_CREATE_VERSION.format(report_id="rep-1"), json={"from_version_number": 1}).status_code
        == 201
    )

    listed = client.get("/api/v3/reports/rep-1/versions")
    assert listed.status_code == 200
    versions = {v["version_number"]: v for v in listed.json()["versions"]}
    assert set(versions) == {1, 2}
    assert versions[1]["status"] == APPROVED
    assert versions[2]["status"] == DRAFT



# ---------------------------------------------------------------------------
# Denial paths & the state guard (§10.2, §13, §26.1)
# ---------------------------------------------------------------------------


def test_iv_s3_a3_processing_entity_staff_have_no_lifecycle_authority(
    client, world, user_provider
) -> None:
    """IV-S3-A3 — a Processing Entity is never an actor on a customer report."""
    _seed_report(world)
    _seed_version(world, version_number=1, status=DRAFT)
    user_provider.set_user(entity_operator_user("pe-1"))

    for version_number, action in ((1, "submit"), (1, "approve")):
        resp = client.post(
            _URL.format(report_id="rep-1", version_number=version_number, action=action)
        )
        assert resp.status_code == 403

    assert _version(world, "rep-1", 1)["status"] == DRAFT
    assert not _events(world, "report.submitted")


def test_iv_s3_a4_denied_and_invalid_transitions_change_nothing(
    client, world, user_provider
) -> None:
    """IV-S3-A4 — a 403/409 leaves no state change and no misleading audit event."""
    _seed_report(world)
    _seed_version(world, version_number=1, status=REVIEWED)

    # (a) authority denial — a member may not approve a reviewed version.
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))
    assert (
        client.post(_URL.format(report_id="rep-1", version_number=1, action="approve")).status_code
        == 403
    )
    assert _version(world, "rep-1", 1)["status"] == REVIEWED

    # (b) state-machine denial — an owner may not approve a DRAFT version.
    _seed_version(world, version_number=2, status=DRAFT, is_current=False)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))
    assert (
        client.post(_URL.format(report_id="rep-1", version_number=2, action="approve")).status_code
        == 409
    )
    assert _version(world, "rep-1", 2)["status"] == DRAFT

    assert not _events(world, "report.approved")


def test_iv_s3_a5_finalize_cannot_skip_approval(client, world, user_provider) -> None:
    """IV-S3-A5 — ``APPROVED`` is not skippable (no DRAFT→FINAL shortcut)."""
    _seed_report(world)
    _seed_version(world, version_number=1, status=DRAFT)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert (
        client.post(_URL.format(report_id="rep-1", version_number=1, action="finalize")).status_code
        == 409
    )
    assert _version(world, "rep-1", 1)["status"] == DRAFT
    assert not _events(world, "report.finalized")


def test_iv_s3_a6_final_is_terminal_for_every_action(client, world, user_provider) -> None:
    """IV-S3-A6 — a FINAL version admits no further transition, for anyone."""
    _seed_report(world)
    frozen = _seed_version(world, version_number=1, status=FINAL)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    for action in ("submit", "request-changes", "reject", "approve", "finalize"):
        resp = client.post(_URL.format(report_id="rep-1", version_number=1, action=action))
        assert resp.status_code == 409, action

    after = _version(world, "rep-1", 1)
    assert after["status"] == FINAL
    assert after["content"] == frozen["content"]

