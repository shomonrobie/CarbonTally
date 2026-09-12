"""Phase 8 S3 — report version lifecycle foundation.

Covers the bounded lifecycle layer: the ratified state machine, server-side
guarded transitions, version-scoped semantics, the customer Owner/Admin
approval boundary, and append-only audit events on the canonical
``audit_trail`` (via the in-memory world — no database access).
"""
from __future__ import annotations

import asyncio

from auth import AuthUser
from domain.report_lifecycle import (
    APPROVE,
    APPROVED,
    CHANGES_REQUESTED,
    DRAFT,
    FINAL,
    FINALIZE,
    NEW_VERSION,
    REJECT,
    REJECTED,
    REQUEST_CHANGES,
    REVIEWED,
    SUBMIT,
    VERSION_STATUSES,
    TransitionNotAllowed,
    allowed_actions,
    can_create_new_version,
    is_immutable,
    is_terminal,
    resolve_transition,
)
from tests.unit.api.fakes import (
    admin_user,
    member_user,
    org_admin_user,
    org_owner_user,
)
from tests.unit.api.route_paths import flatten_router_paths


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


def _events(world, action: str) -> list:
    return [e for e in world.audit._entries if e.action == action]


def _viewer_user(org_id: str, user_id: str, email: str) -> AuthUser:
    """A read-only organisation viewer (org role ``viewer``)."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role="org_viewer",
        role_name="viewer",
        organization_id=org_id,
        is_org_member=True,
    )


# ---------------------------------------------------------------------------
# Pure state machine
# ---------------------------------------------------------------------------


def test_states_are_exactly_the_ratified_six() -> None:
    assert set(VERSION_STATUSES) == {
        "DRAFT",
        "REVIEWED",
        "CHANGES_REQUESTED",
        "REJECTED",
        "APPROVED",
        "FINAL",
    }


def test_no_assurance_or_verification_state_exists() -> None:
    # CarbonTally must never represent its own approval as independent assurance.
    for forbidden in ("VERIFIED", "ASSURED", "CERTIFIED", "AUDITED", "APPROVED_ASSURED"):
        assert forbidden not in VERSION_STATUSES


def test_valid_transitions_resolve() -> None:
    assert resolve_transition(SUBMIT, DRAFT) == REVIEWED
    assert resolve_transition(REQUEST_CHANGES, REVIEWED) == CHANGES_REQUESTED
    assert resolve_transition(REJECT, REVIEWED) == REJECTED
    assert resolve_transition(APPROVE, REVIEWED) == APPROVED
    assert resolve_transition(FINALIZE, APPROVED) == FINAL
    assert resolve_transition(NEW_VERSION, FINAL) == DRAFT


def test_invalid_transitions_are_rejected() -> None:
    # No transition skips a gate.
    for action, state in (
        (APPROVE, DRAFT),          # DRAFT → APPROVED is invalid
        (FINALIZE, REVIEWED),      # approval required before finalization
        (FINALIZE, DRAFT),
        (SUBMIT, REVIEWED),        # already submitted
        (APPROVE, APPROVED),       # cannot re-approve a version
        (SUBMIT, FINAL),           # FINAL is terminal
        (FINALIZE, FINAL),
        (NEW_VERSION, DRAFT),      # a draft is not superseded by a new version
    ):
        try:
            resolve_transition(action, state)
        except TransitionNotAllowed:
            continue
        raise AssertionError(f"{action} from {state} should be rejected")


def test_final_is_terminal_and_approved_is_immutable() -> None:
    assert is_terminal(FINAL) and not is_terminal(APPROVED)
    assert is_immutable(APPROVED) and is_immutable(FINAL)
    # FINAL's only onward action is supersession by a new version.
    assert allowed_actions(FINAL) == (NEW_VERSION,)
    assert allowed_actions(REVIEWED) == (REQUEST_CHANGES, REJECT, APPROVE)
    assert can_create_new_version(APPROVED) and can_create_new_version(FINAL)
    assert not can_create_new_version(DRAFT)


# ---------------------------------------------------------------------------
# Transition correctness (API, in-memory world)
# ---------------------------------------------------------------------------


def _url(report_id: str, version_number: int, action: str) -> str:
    return f"/api/v3/reports/{report_id}/versions/{version_number}/{action}"


def test_lifecycle_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    for fragment in (
        "/api/v3/reports/{report_id}/versions/{version_number}/submit",
        "/api/v3/reports/{report_id}/versions/{version_number}/request-changes",
        "/api/v3/reports/{report_id}/versions/{version_number}/reject",
        "/api/v3/reports/{report_id}/versions/{version_number}/approve",
        "/api/v3/reports/{report_id}/versions/{version_number}/finalize",
    ):
        assert fragment in paths, f"missing lifecycle route: {fragment}"


def test_submit_moves_draft_to_reviewed(client, world, user_provider) -> None:
    _seed_report(world)
    version = _seed_version(world)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(_url("rep-1", 1, "submit"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == REVIEWED
    assert body["status_from"] == DRAFT
    assert body["version_id"] == version["id"]
    assert body["version_number"] == 1
    assert body["is_current"] is True
    assert body["report_id"] == "rep-1"


def test_full_lifecycle_to_final_preserves_version_identity(
    client, world, user_provider
) -> None:
    _seed_report(world)
    version = _seed_version(world)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-1", 1, "submit")).json()["status"] == REVIEWED
    approved = client.post(_url("rep-1", 1, "approve")).json()
    assert approved["status"] == APPROVED
    finalized = client.post(_url("rep-1", 1, "finalize")).json()
    assert finalized["status"] == FINAL

    # Identity is preserved through the whole chain (approval stays version-bound).
    for body in (approved, finalized):
        assert body["version_id"] == version["id"]
        assert body["version_number"] == 1

    stored = asyncio.run(world.report_versions.get_by_number("rep-1", 1))
    assert stored["status"] == FINAL
    assert stored["id"] == version["id"]


def test_approve_requires_reviewed_state(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world)  # DRAFT
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(_url("rep-1", 1, "approve"))

    assert response.status_code == 409
    assert not _events(world, "report.approved")


def test_finalize_requires_approved_state(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(_url("rep-1", 1, "finalize"))

    assert response.status_code == 409
    assert not _events(world, "report.finalized")


def test_final_version_cannot_be_transitioned(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, status=FINAL)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    for action in ("submit", "approve", "finalize", "reject", "request-changes"):
        assert client.post(_url("rep-1", 1, action)).status_code == 409


def test_request_changes_and_reject(client, world, user_provider) -> None:
    _seed_report(world, report_id="rep-1")
    _seed_report(world, report_id="rep-2")
    _seed_version(world, report_id="rep-1", status=REVIEWED)
    _seed_version(world, report_id="rep-2", status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert (
        client.post(_url("rep-1", 1, "request-changes")).json()["status"]
        == CHANGES_REQUESTED
    )
    assert client.post(_url("rep-2", 1, "reject")).json()["status"] == REJECTED


def test_transition_is_version_scoped(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, version_number=1, status=REVIEWED, is_current=False)
    _seed_version(world, version_number=2, status=DRAFT, is_current=True)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    body = client.post(_url("rep-1", 1, "approve")).json()
    assert body["version_number"] == 1

    v1 = asyncio.run(world.report_versions.get_by_number("rep-1", 1))
    v2 = asyncio.run(world.report_versions.get_by_number("rep-1", 2))
    assert v1["status"] == APPROVED
    assert v2["status"] == DRAFT  # untouched


def test_unknown_version_is_404(client, world, user_provider) -> None:
    _seed_report(world)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-1", 9, "submit")).status_code == 404


# ---------------------------------------------------------------------------
# Authorization (server-side; the UI is never the boundary)
# ---------------------------------------------------------------------------


def test_owner_may_approve_and_finalize(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-1", 1, "approve")).status_code == 200
    assert client.post(_url("rep-1", 1, "finalize")).status_code == 200


def test_admin_may_approve_and_finalize(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(org_admin_user("org-a", "admin-a", "admin.a@test"))

    assert client.post(_url("rep-1", 1, "approve")).status_code == 200
    assert client.post(_url("rep-1", 1, "finalize")).status_code == 200


def test_member_cannot_approve_or_review_decide(
    client, world, user_provider
) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    for action in ("approve", "finalize", "request-changes", "reject"):
        assert client.post(_url("rep-1", 1, action)).status_code == 403
    assert not _events(world, "report.approved")


def test_member_may_submit(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world)
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    assert client.post(_url("rep-1", 1, "submit")).status_code == 200


def test_viewer_cannot_perform_lifecycle_actions(
    client, world, user_provider
) -> None:
    _seed_report(world)
    _seed_version(world)
    _seed_version(world, version_number=2, status=REVIEWED, is_current=False)
    user_provider.set_user(_viewer_user("org-a", "viewer-a", "viewer.a@test"))

    assert client.post(_url("rep-1", 1, "submit")).status_code == 403
    assert client.post(_url("rep-1", 2, "approve")).status_code == 403
    assert client.post(_url("rep-1", 2, "finalize")).status_code == 403


def test_internal_staff_cannot_approve(client, world, user_provider) -> None:
    # CarbonTally staff must never approve a customer's own assertion (S3 PO boundary).
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(admin_user())

    assert client.post(_url("rep-1", 1, "approve")).status_code == 403
    assert not _events(world, "report.approved")


def test_cross_org_transition_denied(client, world, user_provider) -> None:
    _seed_report(world, report_id="rep-b", org_id="org-b")
    _seed_version(world, report_id="rep-b", status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-b", 1, "approve")).status_code == 403
    assert not _events(world, "report.approved")


def test_transition_requires_authentication(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world)
    user_provider.set_unauthenticated()

    assert client.post(_url("rep-1", 1, "submit")).status_code == 401


# ---------------------------------------------------------------------------
# Auditability (append-only canonical audit_trail; no second ledger)
# ---------------------------------------------------------------------------


def test_successful_transition_writes_audit_event(
    client, world, user_provider
) -> None:
    _seed_report(world)
    version = _seed_version(world, status=REVIEWED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-1", 1, "approve")).status_code == 200

    entries = _events(world, "report.approved")
    assert len(entries) == 1
    entry = entries[0]
    assert entry.entity_type == "report_versions"
    assert entry.entity_id == version["id"]  # version-bound
    assert entry.actor == "owner-a"          # authenticated principal (never client)
    assert entry.correlation_id == "rep-1"
    assert entry.changed_fields["status_from"] == REVIEWED
    assert entry.changed_fields["status_to"] == APPROVED
    assert entry.changed_fields["version_number"] == 1
    assert entry.before == {"status": REVIEWED}
    assert entry.after == {"status": APPROVED}
    assert entry.category == "report"
    assert entry.origin == "human"
    assert entry.organization_id == "org-a"
    assert entry.occurred_at is not None


def test_each_transition_emits_its_ratified_event(
    client, world, user_provider
) -> None:
    _seed_report(world)
    _seed_version(world)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    client.post(_url("rep-1", 1, "submit"))
    client.post(_url("rep-1", 1, "approve"))
    client.post(_url("rep-1", 1, "finalize"))

    actions = [e.action for e in world.audit._entries]
    assert "report.review_submitted" in actions
    assert "report.approved" in actions
    assert "report.finalized" in actions


def test_invalid_transition_writes_no_audit_event(
    client, world, user_provider
) -> None:
    _seed_report(world)
    _seed_version(world)  # DRAFT
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    assert client.post(_url("rep-1", 1, "finalize")).status_code == 409
    assert world.audit._entries == []


def test_denied_transition_writes_no_audit_event(
    client, world, user_provider
) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    assert client.post(_url("rep-1", 1, "approve")).status_code == 403
    assert world.audit._entries == []


# ---------------------------------------------------------------------------
# Post-approval / post-final change → NEW version (immutability)
# ---------------------------------------------------------------------------


def test_new_version_from_final_creates_draft_and_leaves_final_untouched(
    client, world, user_provider
) -> None:
    _seed_report(world)
    final = _seed_version(world, version_number=1, status=FINAL)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(
        "/api/v3/reports/rep-1/versions",
        json={"from_version_number": 1, "reason": "post-final correction"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["version_number"] == 2
    assert body["status"] == DRAFT
    assert body["status_from"] == FINAL
    assert body["from_version_number"] == 1

    v1 = asyncio.run(world.report_versions.get_by_number("rep-1", 1))
    v2 = asyncio.run(world.report_versions.get_by_number("rep-1", 2))
    assert v1["status"] == FINAL and v1["id"] == final["id"]  # never mutated
    assert v1["content"] == final["content"]
    assert v2["status"] == DRAFT and v2["is_current"] is True
    assert v1["is_current"] is False  # superseded (derived, not stored)
    assert _events(world, "report.version_created")


def test_new_version_from_approved_preserves_the_approved_version(
    client, world, user_provider
) -> None:
    _seed_report(world)
    approved = _seed_version(world, version_number=1, status=APPROVED)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(
        "/api/v3/reports/rep-1/versions", json={"from_version_number": 1}
    )
    assert response.status_code == 201

    v1 = asyncio.run(world.report_versions.get_by_number("rep-1", 1))
    assert v1["status"] == APPROVED and v1["id"] == approved["id"]


def test_new_version_from_draft_is_rejected(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world)  # DRAFT
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(
        "/api/v3/reports/rep-1/versions", json={"from_version_number": 1}
    )
    assert response.status_code == 409


def test_new_version_requires_org_access(client, world, user_provider) -> None:
    _seed_report(world, report_id="rep-b", org_id="org-b")
    _seed_version(world, report_id="rep-b", status=FINAL)
    user_provider.set_user(org_owner_user("org-a", "owner-a", "owner.a@test"))

    response = client.post(
        "/api/v3/reports/rep-b/versions", json={"from_version_number": 1}
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Existing surfaces expose lifecycle state (additive, contract-safe)
# ---------------------------------------------------------------------------


def test_version_listing_exposes_status(client, world, user_provider) -> None:
    _seed_report(world)
    _seed_version(world, status=REVIEWED)
    user_provider.set_user(member_user("org-a", "member-a", "member.a@test"))

    body = client.get("/api/v3/reports/rep-1/versions").json()
    assert body["versions"][0]["status"] == REVIEWED





