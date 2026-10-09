"""CT-MP-SUB-004 NOTIFICATION-IMPLEMENT-04 — Manual Processing lifecycle
notifications (N1-N4).

Focused, self-verifying coverage for the PO-authorised Manual Processing
lifecycle notification set:

* **N1** MP work assigned/routed to a Processing Entity -> that entity's
  ACTIVE staff (in-app, mandatory, idempotent, no email);
* **N2** MP item/batch assigned to a specific CarbonTally internal validator
  -> that validator (reusing the pre-existing ``work_item.assigned`` producer
  at item level; closing the batch level);
* **N3** a document/batch enters Manual Processing -> the ONE responsible
  consultant resolved server-side (never a broadcast; fail-safe + audited);
* **N4** the terminal validated state (CarbonTally CT-QC approval) -> the
  ORIGINAL uploader (never emitted at PE completion).

Plus the mandated negatives: coverage allocation/release stay audit-only, no
email/delivery path exists, and every non-recipient actor is denied.

No database is touched: the in-memory fakes only.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from domain.entity import ProcessingEntity
from domain.staff import StaffProfile, StaffRole
from services import manual_processing_notifications as mpn
from services.manual_processing_routing import ManualProcessingRouter
from services.work_items import ops_assign_item, pe_complete_item
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_admin_user,
    org_owner_user,
    staff_user,
)

OPS = "/api/v3/ops"
PE = "/api/v3/pe"
ADMIN_BASE = "/api/v3/admin/manual-processing"
NOTIFICATIONS = "/api/v3/notifications"

_MODULE = Path(mpn.__file__)


@dataclass
class _Job:
    """Minimal automatic-processing job stand-in for the fallback router."""

    id: str = "job-1"
    organization_id: str = "org-a"
    stage: str = "blocked"
    manual_review_reason: str | None = "extraction incomplete"
    last_error: str | None = None
    source_item_id: str | None = "item-1"
    file_name: str = "invoice.pdf"


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_entity(world, entity_id: str = "pe-1", *, status: str = "active") -> None:
    asyncio.run(
        world.entities.save(
            ProcessingEntity(id=entity_id, name=f"PE {entity_id}", status=status)
        )
    )


def _seed_pe_staff(
    world, *, entity_id: str, user_id: str, is_active: bool = True
) -> None:
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name=user_id,
            last_name="Operator",
            email=f"{user_id}@pe.test",
            entity_id=entity_id,
            is_active=is_active,
        )
    )


def _seed_internal_staff(
    world, user_id: str, *, perms=None, role_id: str | None = None
) -> None:
    rid = role_id or f"role-{user_id}"
    world.staff.seed_role(StaffRole(id=rid, name=rid, permissions=perms or {}))
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name=user_id,
            last_name="Staff",
            email=f"{user_id}@carbontally.test",
            role_id=rid,
        )
    )


def _seed_file(world, file_id: str, uploaded_by: str, org: str = "org-a") -> None:
    world.files.add_file(
        SimpleNamespace(
            id=file_id,
            organization_id=org,
            name="invoice.pdf",
            uploaded_by=uploaded_by,
        )
    )


def _seed_item(world, *, item_id: str = "item-1", org: str = "org-a", **kw):
    return world.manual_extraction.seed_item(
        item_id, org, "invoice.pdf", **kw
    )


def _rows(world) -> list[dict]:
    return world.notifications.rows  # noqa: SLF001 (test fake)


def _rows_of_type(world, notification_type: str) -> list[dict]:
    return [r for r in _rows(world) if r["notification_type"] == notification_type]


def _recipients(world, notification_type: str) -> list[str]:
    return sorted(r["recipient_id"] for r in _rows_of_type(world, notification_type))


def _actions(world) -> list[str]:
    return [e.action for e in world.audit._entries]  # noqa: SLF001 (test fake)


def _seed_consultant_relationship(
    world,
    *,
    firm_id: str = "firm-1",
    principal: str = "u-principal",
    members: tuple[str, ...] = ("u-principal", "u-colleague"),
    client_created_by: str | None = None,
    org: str = "org-a",
    with_relationship: bool = True,
) -> None:
    """Seed a firm, its active members and (optionally) an ACTIVE client grant."""
    world.consultants.seed_profile(firm_id, principal, "Advisory Ltd", is_active=True)
    for member in members:
        world.consultants.seed_firm_member(
            firm_id, member, role="consultant", is_active=True,
            can_manage_clients=True, can_upload_documents=True,
        )
    if with_relationship:
        world.consultants.seed_client(
            f"cc-{org}", firm_id, org, "Client Org", status="active",
            created_by=client_created_by,
        )


def _mp_preconditions(world, *, org: str = "org-a", entity_id: str = "pe-1") -> None:
    """Entitlement + governance + configured processor for the fallback router."""
    _seed_entity(world, entity_id)
    world.manual_processing.seed_entitlement(org)
    world.manual_processing.seed_grant("organization", org)
    world.manual_processing.seed_processor(
        "organization", org, processing_entity_id=entity_id
    )


def _route(world, job: "_Job | None" = None) -> dict:
    return asyncio.run(
        ManualProcessingRouter(world.bundle()).route_failed_job(job or _Job())
    )


def _as_qc(client, world, user_provider, item_id, *, approved: bool = True):
    """Drive the real CT-QC decision endpoint as internal ``can_qc`` staff."""
    _seed_internal_staff(world, "u-qc", perms={"can_qc": True})
    user_provider.set_user(staff_user("u-qc"))
    return client.post(
        f"{OPS}/qc/items/{item_id}/decision",
        json={"quality_score": 90, "approved": approved, "qc_notes": "verified"},
    )


# ---------------------------------------------------------------------------
# N1 — Processing Entity assignment
# ---------------------------------------------------------------------------


class TestN1PeAssignment:
    """N1: PE assignment notifies the ASSIGNED entity's ACTIVE staff only."""

    def test_automatic_fallback_routing_notifies_the_assigned_pe_staff(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-a")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-b")
        _seed_item(world, item_id="item-1")
        outcome = _route(world)
        assert outcome["routed"] is True
        assert _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT) == [
            "u-pe1-a", "u-pe1-b",
        ]

    def test_an_inactive_pe_staff_member_is_not_notified(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-active")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-gone", is_active=False)
        _seed_item(world, item_id="item-1")
        _route(world)
        assert _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT) == [
            "u-pe1-active"
        ]

    def test_an_unrelated_processing_entity_is_not_notified(self, world):
        _mp_preconditions(world)
        _seed_entity(world, "pe-2")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_pe_staff(world, entity_id="pe-2", user_id="u-pe2")
        _seed_item(world, item_id="item-1")
        _route(world)
        recipients = _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)
        assert recipients == ["u-pe1"]
        assert "u-pe2" not in recipients

    def test_internal_staff_are_never_n1_recipients(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_internal_staff(world, "u-ops", perms={"can_process": True})
        _seed_item(world, item_id="item-1")
        _route(world)
        assert "u-ops" not in _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)

    def test_duplicate_routing_does_not_duplicate_the_notification(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        _route(world)
        _route(world)  # worker retry / re-queue: idempotent by construction
        assert len(_rows_of_type(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)) == 1
        assert len(asyncio.run(world.manual_extraction.work_item_history("item-1"))) == 1

    def test_ops_item_assignment_to_a_pe_notifies_that_entities_staff(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id="u-owner",
                target_entity_id="pe-1",
            )
        )
        assert _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT) == ["u-pe1"]

    def test_a_second_assignment_to_the_same_entity_is_not_re_notified(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        for _ in range(2):
            asyncio.run(
                ops_assign_item(
                    world.bundle(),
                    item_id="item-1",
                    actor_user_id="u-owner",
                    target_entity_id="pe-1",
                )
            )
        assert len(_rows_of_type(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)) == 1

    def test_assignment_survives_a_notification_failure(self, world):
        """The D38 assignment is authoritative; notification failure is not."""
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")

        async def _boom(*_a, **_k):
            raise RuntimeError("notification store unavailable")

        world.notifications.create_idempotent = _boom
        result = asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id="u-owner",
                target_entity_id="pe-1",
            )
        )
        assert result["changed"] is True
        current = asyncio.run(world.manual_extraction.work_item_current("item-1"))
        assert current is not None
        assert str(current["processing_entity_id"]) == "pe-1"

    def test_batch_assignment_to_a_pe_notifies_that_entities_staff(
        self, world, client, user_provider
    ):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_internal_staff(
            world, "u-mgr", perms={"can_manage_staff": True, "can_process": True}
        )
        batch = _seed_item(world, item_id="item-1").batch_id
        user_provider.set_user(staff_user("u-mgr"))
        resp = client.post(
            f"{OPS}/batches/{batch}/assign", json={"entity_id": "pe-1"}
        )
        assert resp.status_code == 200, resp.text
        assert _recipients(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT) == ["u-pe1"]


# ---------------------------------------------------------------------------
# N2 — CarbonTally internal validator assignment
# ---------------------------------------------------------------------------


class TestN2ValidatorAssignment:
    """N2: reuses ``work_item.assigned`` at item level; closes the batch level."""

    def _assign_internal(self, world, *, assignee: str, actor: str = "u-owner"):
        world.manual_extraction.seed_internal_staff(assignee)
        return asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id=actor,
                target_user_id=assignee,
            )
        )

    def test_item_assignment_to_a_validator_creates_work_item_assigned(self, world):
        _seed_item(world, item_id="item-1")
        self._assign_internal(world, assignee="u-validator")
        assert _recipients(world, "work_item.assigned") == ["u-validator"]

    def test_the_wrong_validator_does_not_receive_it(self, world):
        _seed_item(world, item_id="item-1")
        self._assign_internal(world, assignee="u-validator")
        assert "u-other-validator" not in _recipients(world, "work_item.assigned")

    def test_a_self_claim_does_not_notify_the_claimer(self, world):
        _seed_item(world, item_id="item-1")
        self._assign_internal(world, assignee="u-validator", actor="u-validator")
        assert _rows_of_type(world, "work_item.assigned") == []

    def test_a_duplicate_assignment_does_not_duplicate_the_notification(self, world):
        _seed_item(world, item_id="item-1")
        self._assign_internal(world, assignee="u-validator")
        self._assign_internal(world, assignee="u-validator")
        assert len(_rows_of_type(world, "work_item.assigned")) == 1

    def test_a_pe_assignment_never_produces_work_item_assigned(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id="u-owner",
                target_entity_id="pe-1",
            )
        )
        assert _rows_of_type(world, "work_item.assigned") == []

    def test_batch_assignment_to_an_internal_validator_notifies_that_person(
        self, world, client, user_provider
    ):
        _seed_internal_staff(
            world, "u-mgr", perms={"can_manage_staff": True, "can_process": True}
        )
        _seed_internal_staff(world, "u-validator", perms={"can_process": True})
        batch = _seed_item(world, item_id="item-1").batch_id
        user_provider.set_user(staff_user("u-mgr"))
        resp = client.post(
            f"{OPS}/batches/{batch}/assign", json={"assigned_to": "u-validator"}
        )
        assert resp.status_code == 200, resp.text
        assert _recipients(world, mpn.NOTIFICATION_TYPE_VALIDATOR_ASSIGNMENT) == [
            "u-validator"
        ]

    def test_a_self_batch_assignment_emits_nothing(self, world, client, user_provider):
        _seed_internal_staff(
            world, "u-mgr", perms={"can_manage_staff": True, "can_process": True}
        )
        batch = _seed_item(world, item_id="item-1").batch_id
        user_provider.set_user(staff_user("u-mgr"))
        resp = client.post(
            f"{OPS}/batches/{batch}/assign", json={"assigned_to": "u-mgr"}
        )
        assert resp.status_code == 200, resp.text
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_VALIDATOR_ASSIGNMENT) == []

    def test_an_internal_assignment_never_notifies_a_processing_entity(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        self._assign_internal(world, assignee="u-validator")
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT) == []


# ---------------------------------------------------------------------------
# N3 — Manual Processing entry -> responsible consultant
# ---------------------------------------------------------------------------


class TestN3ConsultantEntry:
    """N3: ONE responsible consultant; never a broadcast; fail-safe when unclear."""

    def test_routing_entry_notifies_the_relationship_owner_only(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(
            world, members=("u-principal", "u-colleague"), client_created_by="u-colleague"
        )
        _seed_item(world, item_id="item-1")
        _route(world)
        assert _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == ["u-colleague"]

    def test_the_firm_principal_is_used_when_no_member_owns_the_relationship(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(world, members=("u-principal", "u-colleague"))
        _seed_item(world, item_id="item-1")
        _route(world)
        assert _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == ["u-principal"]

    def test_other_firm_members_are_never_notified(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(
            world, members=("u-principal", "u-colleague", "u-manager"),
            client_created_by="u-principal",
        )
        _seed_item(world, item_id="item-1")
        _route(world)
        recipients = _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY)
        assert recipients == ["u-principal"]
        assert "u-colleague" not in recipients and "u-manager" not in recipients

    def test_item_provenance_firm_wins_over_another_active_firm(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(world, firm_id="firm-1", principal="u-p1")
        _seed_consultant_relationship(
            world, firm_id="firm-2", principal="u-p2", members=("u-p2",),
            client_created_by="u-p2",
        )
        _seed_item(world, item_id="item-1")
        asyncio.run(
            world.manual_extraction.record_consultant_provenance(
                "item-1", firm_id="firm-2", processing_mode="manual"
            )
        )
        _route(world)
        assert _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == ["u-p2"]

    def test_multiple_relationships_fail_safe_with_an_audit_record(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(world, firm_id="firm-1", principal="u-p1")
        _seed_consultant_relationship(
            world, firm_id="firm-2", principal="u-p2", members=("u-p2",)
        )
        _seed_item(world, item_id="item-1")
        _route(world)
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == []
        assert mpn.AUDIT_CONSULTANT_UNRESOLVED in _actions(world)

    def test_no_consultant_relationship_notifies_nobody_and_is_not_an_ambiguity(
        self, world
    ):
        _mp_preconditions(world)
        _seed_item(world, item_id="item-1")
        _route(world)
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == []
        assert mpn.AUDIT_CONSULTANT_UNRESOLVED not in _actions(world)

    def test_explicit_batch_creation_notifies_the_responsible_consultant(
        self, world, client, user_provider
    ):
        world.manual_processing.seed_entitlement("org-a")
        world.manual_processing.seed_grant("organization", "org-a")
        _seed_consultant_relationship(world, client_created_by="u-colleague")
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.post(
            "/api/v3/manual-extraction/batches?organization_id=org-a",
            json={"batch_name": "MP batch"},
        )
        assert resp.status_code == 201, resp.text
        assert _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY) == ["u-colleague"]

    def test_entry_notification_is_idempotent_for_the_same_item(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(world, client_created_by="u-colleague")
        _seed_item(world, item_id="item-1")
        asyncio.run(
            mpn.notify_manual_processing_entry(
                world.bundle(), organization_id="org-a", item_id="item-1"
            )
        )
        asyncio.run(
            mpn.notify_manual_processing_entry(
                world.bundle(), organization_id="org-a", item_id="item-1"
            )
        )
        assert len(_rows_of_type(world, mpn.NOTIFICATION_TYPE_MP_ENTRY)) == 1


# ---------------------------------------------------------------------------
# N4 — terminal validated state -> original uploader
# ---------------------------------------------------------------------------


class TestN4Completion:
    """N4: only the CT-QC approved terminal state notifies the original uploader."""

    def test_ct_qc_approval_notifies_the_original_uploader(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        resp = _as_qc(client, world, user_provider, "item-1")
        assert resp.status_code == 200, resp.text
        assert resp.json()["item"]["status"] == "ct_qc_approved"
        assert _recipients(world, mpn.NOTIFICATION_TYPE_COMPLETION) == ["u-uploader"]

    def test_a_consultant_uploader_is_linked_to_the_consultant_workspace(
        self, world, client, user_provider
    ):
        world.consultants.seed_profile("firm-1", "u-principal", is_active=True)
        world.consultants.seed_firm_member("firm-1", "u-uploader", is_active=True)
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        rows = _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION)
        assert [r["link"] for r in rows] == [mpn.LINK_CONSULTANT_WORKSPACE]

    def test_an_organisation_uploader_is_linked_to_the_processing_item(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        rows = _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION)
        assert [r["link"] for r in rows] == ["/processing/item-1"]

    def test_a_rejection_never_emits_a_completion_notification(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        resp = _as_qc(client, world, user_provider, "item-1", approved=False)
        assert resp.status_code == 200, resp.text
        assert resp.json()["item"]["status"] == "ct_qc_rejected"
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION) == []

    def test_reassignment_to_a_processing_entity_does_not_change_the_uploader(
        self, world, client, user_provider
    ):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id="u-owner",
                target_entity_id="pe-1",
            )
        )
        _as_qc(client, world, user_provider, "item-1")
        assert _recipients(world, mpn.NOTIFICATION_TYPE_COMPLETION) == ["u-uploader"]
        assert "u-pe1" not in _recipients(world, mpn.NOTIFICATION_TYPE_COMPLETION)

    def test_pe_work_item_completion_emits_no_completion_notification(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", file_id="file-1")
        asyncio.run(
            ops_assign_item(
                world.bundle(),
                item_id="item-1",
                actor_user_id="u-owner",
                target_entity_id="pe-1",
            )
        )
        asyncio.run(
            pe_complete_item(
                world.bundle(),
                item_id="item-1",
                entity_id="pe-1",
                actor_user_id="u-pe1",
            )
        )
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION) == []

    def test_pe_qc_approval_emits_no_completion_notification(self, world):
        """PE QC approval is NOT the terminal state (CT-QC still required)."""
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", file_id="file-1")
        asyncio.run(
            world.manual_extraction.set_item_status("item-1", "pe_qc_approved")
        )
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION) == []

    def test_an_item_without_a_file_link_notifies_nobody(
        self, world, client, user_provider
    ):
        _seed_item(world, item_id="item-1", status="reviewed")
        resp = _as_qc(client, world, user_provider, "item-1")
        assert resp.status_code == 200, resp.text
        assert _rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION) == []

    def test_a_duplicate_decision_does_not_duplicate_the_notification(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        second = _as_qc(client, world, user_provider, "item-1")
        assert second.status_code == 409, second.text
        assert len(_rows_of_type(world, mpn.NOTIFICATION_TYPE_COMPLETION)) == 1

    def test_a_client_organisation_user_is_never_the_completion_recipient(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        recipients = _recipients(world, mpn.NOTIFICATION_TYPE_COMPLETION)
        assert "owner-a" not in recipients and "admin-a" not in recipients


# ---------------------------------------------------------------------------
# Event keys, resolvers and the API retrieval path
# ---------------------------------------------------------------------------


class TestEventKeysAndResolvers:
    """Deterministic, server-generated keys; fail-safe resolvers."""

    def test_event_keys_are_deterministic_and_namespaced(self):
        assert mpn.pe_assignment_event_key(
            item_id="i", assignment_id="a"
        ) == "manual_processing.pe_assigned:item:i:a"
        assert mpn.pe_batch_assignment_event_key(
            batch_id="b", entity_id="pe"
        ) == "manual_processing.pe_assigned:batch:b:pe"
        assert mpn.validator_batch_assignment_event_key(
            batch_id="b", user_id="u"
        ) == "manual_processing.validator_assigned:batch:b:u"
        assert mpn.mp_entry_item_event_key(item_id="i") == (
            "manual_processing.entered:item:i"
        )
        assert mpn.mp_entry_batch_event_key(batch_id="b") == (
            "manual_processing.entered:batch:b"
        )
        assert mpn.completion_event_key(item_id="i") == (
            "manual_processing.completed:item:i"
        )

    def test_pe_assignment_key_moves_with_the_assignment_row(self):
        first = mpn.pe_assignment_event_key(item_id="i", assignment_id="a-1")
        second = mpn.pe_assignment_event_key(item_id="i", assignment_id="a-2")
        assert first != second

    def test_the_pe_recipient_resolver_returns_only_that_entity(self, world):
        _seed_entity(world, "pe-1")
        _seed_entity(world, "pe-2")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_pe_staff(world, entity_id="pe-2", user_id="u-pe2")
        _seed_internal_staff(world, "u-ops", perms={"can_view_all": True})
        assert asyncio.run(mpn.pe_staff_recipients(world.bundle(), "pe-1")) == ["u-pe1"]

    def test_the_pe_recipient_resolver_refuses_a_missing_entity(self, world):
        assert asyncio.run(mpn.pe_staff_recipients(world.bundle(), None)) == []

    def test_the_consultant_resolver_needs_a_relationship(self, world):
        assert asyncio.run(
            mpn.resolve_responsible_consultant(world.bundle(), organization_id="org-a")
        ) == (None, "no_consultant_relationship")

    def test_the_consultant_resolver_refuses_multiple_relationships(self, world):
        _seed_consultant_relationship(world, firm_id="firm-1", principal="u-p1")
        _seed_consultant_relationship(
            world, firm_id="firm-2", principal="u-p2", members=("u-p2",)
        )
        user, reason = asyncio.run(
            mpn.resolve_responsible_consultant(world.bundle(), organization_id="org-a")
        )
        assert user is None
        assert reason == "multiple_consultant_relationships"

    def test_the_uploader_resolver_returns_none_without_a_file_link(self, world):
        assert asyncio.run(mpn.resolve_uploader(world.bundle(), _seed_item(world))) is None

    def test_the_uploader_resolver_reads_the_durable_upload_record(self, world):
        _seed_file(world, "file-1", "u-uploader")
        item = _seed_item(world, item_id="item-1", file_id="file-1")
        assert asyncio.run(mpn.resolve_uploader(world.bundle(), item)) == "u-uploader"

    def test_a_recipient_can_retrieve_the_notification_through_the_api(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        user_provider.set_user(member_user("org-a", "u-uploader", "u@test"))
        resp = client.get(NOTIFICATIONS)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert [n["notification_type"] for n in body["notifications"]] == [
            mpn.NOTIFICATION_TYPE_COMPLETION
        ]

    def test_another_user_cannot_see_the_uploaders_notification(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        user_provider.set_user(member_user("org-a", "u-other", "o@test"))
        resp = client.get(NOTIFICATIONS)
        assert resp.status_code == 200, resp.text
        assert resp.json()["notifications"] == []
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Security / authorization negatives
# ---------------------------------------------------------------------------


class TestSecurityNegatives:
    """Every unauthorised actor must be DENIED a lifecycle notification."""

    def test_a_cross_tenant_consultant_is_not_notified_for_another_client(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(
            world, members=("u-owner-a", "u-principal"),
            client_created_by="u-owner-a",
        )
        _seed_consultant_relationship(
            world, firm_id="firm-other", principal="u-owner-b",
            members=("u-owner-b",), org="org-b", client_created_by="u-owner-b",
        )
        _seed_item(world, item_id="item-1", org="org-a")
        _route(world)
        recipients = _recipients(world, mpn.NOTIFICATION_TYPE_MP_ENTRY)
        assert recipients == ["u-owner-a"]
        assert "u-owner-b" not in recipients

    def test_an_unrelated_consultant_is_not_notified_by_a_pe_assignment(self, world):
        _mp_preconditions(world)
        _seed_consultant_relationship(world, client_created_by="u-consultant")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        _route(world)
        assert "u-consultant" not in _recipients(
            world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT
        )

    def test_an_unrelated_internal_staff_member_is_not_notified(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_internal_staff(world, "u-unrelated", perms={"can_view_all": True})
        _seed_item(world, item_id="item-1")
        _route(world)
        assert "u-unrelated" not in _recipients(
            world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT
        )

    def test_a_wrong_uploader_is_not_treated_as_the_uploader(
        self, world, client, user_provider
    ):
        _seed_file(world, "file-1", "u-real-uploader")
        _seed_item(world, item_id="item-1", status="reviewed", file_id="file-1")
        _as_qc(client, world, user_provider, "item-1")
        recipients = _recipients(world, mpn.NOTIFICATION_TYPE_COMPLETION)
        assert recipients == ["u-real-uploader"]

    def test_the_producer_entry_points_accept_no_recipient_or_event_key(self, world):
        """A caller cannot nominate a recipient or forge an event key."""
        _seed_item(world, item_id="item-1")
        for kwargs in (
            {"recipient_id": "u-attacker"},
            {"event_key": "forged"},
            {"notification_target": "u-attacker"},
        ):
            try:
                asyncio.run(
                    mpn.notify_manual_processing_entry(
                        world.bundle(), organization_id="org-a", item_id="item-1",
                        **kwargs,
                    )
                )
            except TypeError:
                continue
            raise AssertionError(f"accepted a forged field: {kwargs}")

    def test_a_forged_recipient_in_an_api_body_is_never_used(
        self, world, client, user_provider
    ):
        _seed_internal_staff(
            world, "u-mgr", perms={"can_manage_staff": True, "can_process": True}
        )
        batch = _seed_item(world, item_id="item-1").batch_id
        user_provider.set_user(staff_user("u-mgr"))
        resp = client.post(
            f"{OPS}/batches/{batch}/assign",
            json={
                "assigned_to": "u-validator",
                "recipient_id": "u-attacker",
                "event_key": "forged",
            },
        )
        assert resp.status_code in (200, 422), resp.text
        assert all(
            r["recipient_id"] != "u-attacker" for r in _rows(world)
        ), _rows(world)
        assert "forged" not in world.notifications.event_keys()


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    """One notification per (recipient, event); one per authorised recipient."""

    def test_same_event_and_recipient_yields_one_notification(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_item(world, item_id="item-1")
        for _ in range(2):
            asyncio.run(
                mpn.notify_pe_item_assignment(
                    world.bundle(), item_id="item-1", entity_id="pe-1",
                    assignment_id="a-1",
                )
            )
        assert len(_rows_of_type(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)) == 1

    def test_same_event_and_multiple_recipients_yields_one_each(self, world):
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-a")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1-b")
        _seed_item(world, item_id="item-1")
        asyncio.run(
            mpn.notify_pe_item_assignment(
                world.bundle(), item_id="item-1", entity_id="pe-1",
                assignment_id="a-1",
            )
        )
        rows = _rows_of_type(world, mpn.NOTIFICATION_TYPE_PE_ASSIGNMENT)
        assert len(rows) == 2
        assert len({r["event_key"] for r in rows}) == 1
        assert sorted(r["recipient_id"] for r in rows) == ["u-pe1-a", "u-pe1-b"]

    def test_the_event_key_unique_constraint_semantics_are_mirrored(self, world):
        key = mpn.pe_assignment_event_key(item_id="item-1", assignment_id="a-1")
        for _ in range(3):
            asyncio.run(
                world.notifications.create_idempotent(
                    "u-pe1", key, notification_type="x", title="t", message="m"
                )
            )
        assert len(world.notifications.rows) == 1

    def test_a_different_recipient_gets_its_own_row_for_the_same_event(self, world):
        key = mpn.completion_event_key(item_id="item-1")
        for user in ("u-a", "u-b"):
            asyncio.run(
                world.notifications.create_idempotent(
                    user, key, notification_type="x", title="t", message="m"
                )
            )
        assert len(world.notifications.rows) == 2


# ---------------------------------------------------------------------------
# No email / in-app only  ·  coverage allocation/release separation
# ---------------------------------------------------------------------------


class TestChannelAndCoverageSeparation:
    """The in-app-only rule and the audit-only coverage rule are provable."""

    def test_the_producer_module_has_no_email_or_delivery_path(self):
        """Only the durable in-app row is ever created: no email channel code."""
        source = _MODULE.read_text(encoding="utf-8")
        for token in (
            "record_delivery",
            "email_for_user",
            "send_email",
            "smtplib",
            "import resend",
            "smtp.",
        ):
            assert token not in source, token
        # ...and the only notification write is the idempotent in-app insert.
        assert "create_idempotent" in source
        assert "notifications.create(" not in source

    def test_every_manual_processing_row_is_in_app_and_actor_domained(self, world):
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_consultant_relationship(world, client_created_by="u-consultant")
        _seed_file(world, "file-1", "u-uploader")
        _seed_item(world, item_id="item-1", file_id="file-1")
        _route(world)
        assert _rows(world), "expected the lifecycle events to have fired"
        for row in _rows(world):
            assert row["recipient_type"] == "user"
            assert row["actor_domain"] is not None
            assert row["event_key"] is not None
            assert row["notification_type"].startswith("manual_processing.")

    def test_the_producer_module_contains_no_allocation_or_release_vocabulary(self):
        source = _MODULE.read_text(encoding="utf-8").lower()
        for token in ("allocation_created", "allocation_released", "coverage"):
            assert token not in source, token

    def test_routing_never_produces_a_coverage_notification(self, world):
        """Routing touches coverage/allocation but must emit no such event."""
        _mp_preconditions(world)
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        world.manual_processing.seed_active_client_grant("org-a", "firm-1", "cc-a")
        _seed_item(world, item_id="item-1")
        _route(world)
        for row in _rows(world):
            assert "allocation" not in (row["notification_type"] or "")
            assert "release" not in (row["notification_type"] or "")

    def test_no_notification_is_emitted_for_a_blocked_route(self, world):
        """No assignment and no MP entry => no notification at all."""
        _seed_entity(world, "pe-1")
        _seed_pe_staff(world, entity_id="pe-1", user_id="u-pe1")
        _seed_consultant_relationship(world, client_created_by="u-consultant")
        _seed_item(world, item_id="item-1")
        outcome = _route(world)  # not entitled / not enabled
        assert outcome["routed"] is False
        assert _rows(world) == []
