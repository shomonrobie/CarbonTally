"""V3 operations authorization (Phase 8) — unit tests for operations_auth.

Covers the server-side authorization chain at the guard level:
staff identity (``require_staff``), role permissions
(``ensure_staff_permission``), CarbonTally-internal vs processing-entity scope
(``require_internal_staff`` / ``require_entity_scope``) and the batch/review
scoping guards (``ensure_batch_operator_access`` /
``ensure_entity_review_scope``). Endpoint-level coverage lives in
``test_v3_operations.py``.
"""
from __future__ import annotations

from typing import Optional

import pytest
from fastapi import HTTPException

from api.operations_auth import (
    StaffContext,
    ensure_batch_operator_access,
    ensure_entity_review_scope,
    ensure_staff_permission,
    require_entity_scope,
    require_internal_staff,
    require_staff,
)
from domain.operations import ReviewItem
from domain.staff import StaffProfile, StaffRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profile(
    user_id: str = "u-op",
    *,
    role_id: Optional[str] = "role-operator",
    entity_id: Optional[str] = None,
    is_active: bool = True,
) -> StaffProfile:
    return StaffProfile(
        id=f"sp-{user_id}",
        user_id=user_id,
        first_name="Ada",
        last_name="Lovelace",
        email=f"{user_id}@carbontally.test",
        role_id=role_id,
        entity_id=entity_id,
        is_active=is_active,
    )


def _context(profile: StaffProfile, permissions: Optional[dict] = None) -> StaffContext:
    return StaffContext(profile=profile, permissions=permissions or {})


def _review(entity_id: Optional[str] = None) -> ReviewItem:
    return ReviewItem(
        id="rv-1",
        organization_id="org-a",
        file_name="invoice.pdf",
        status="pending",
        priority=1,
        entity_id=entity_id,
    )


async def _bootstrap(world) -> None:
    """Seed the staff roles + staff profiles the ops guards resolve.

    Staff permissions live on ``staff_roles`` (``staff_profiles.role_id`` →
    ``staff_roles.id``) — the authoritative staff-role model.
    """
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_role(
        StaffRole(id="role-reviewer", name="reviewer", permissions={"can_review": True})
    )
    world.staff.seed_role(
        StaffRole(
            id="role-manager",
            name="manager",
            permissions={"can_manage_staff": True, "can_view_all": True},
        )
    )
    world.staff.seed_profile(_profile("u-op", role_id="role-operator"))
    world.staff.seed_profile(_profile("u-rev", role_id="role-reviewer"))
    world.staff.seed_profile(_profile("u-mgr", role_id="role-manager"))
    world.staff.seed_profile(_profile("u-ent", role_id="role-reviewer", entity_id="entity-1"))



# ---------------------------------------------------------------------------
# Async guards (against the in-memory world)
# ---------------------------------------------------------------------------


async def test_require_staff_resolves_role_permissions(world) -> None:
    from auth import AuthUser

    await _bootstrap(world)
    user = AuthUser(
        user_id="u-op",
        email="op@carbontally.test",
        role="staff",
        role_name="operator",
        permissions={},
        is_active=True,
        is_staff=True,
        is_admin=False,
    )
    context = await require_staff(current_user=user, repos=world.bundle())
    assert context.profile.user_id == "u-op"
    assert context.permissions.get("can_process") is True


async def test_require_staff_rejects_missing_profile(world) -> None:
    from auth import AuthUser

    await _bootstrap(world)
    user = AuthUser(
        user_id="u-nobody",
        email="nobody@carbontally.test",
        role="staff",
        role_name="staff",
        permissions={},
        is_active=True,
        is_staff=True,
        is_admin=False,
    )
    with pytest.raises(HTTPException) as exc_info:
        await require_staff(current_user=user, repos=world.bundle())
    assert exc_info.value.status_code == 403


async def test_ensure_batch_operator_access_allows_assigned(world) -> None:
    await _bootstrap(world)
    batch = await world.manual_extraction.create_batch("org-a", "B1")
    await world.manual_extraction.update_batch(batch.id, status="in_progress", assigned_to="u-op")
    context = _context(_profile("u-op"), {"can_process": True})
    result = await ensure_batch_operator_access(context, world.bundle(), batch.id)
    assert result.id == batch.id


async def test_ensure_batch_operator_access_allows_open(world) -> None:
    await _bootstrap(world)
    batch = await world.manual_extraction.create_batch("org-a", "B1")
    context = _context(_profile("u-op"), {"can_process": True})
    result = await ensure_batch_operator_access(context, world.bundle(), batch.id)
    assert result.id == batch.id  # unassigned open batch = self-serve


async def test_ensure_batch_operator_access_denies_other_operator(world) -> None:
    await _bootstrap(world)
    batch = await world.manual_extraction.create_batch("org-a", "B1")
    await world.manual_extraction.update_batch(batch.id, status="in_progress", assigned_to="u-other")
    context = _context(_profile("u-op"), {"can_process": True})
    with pytest.raises(HTTPException) as exc_info:
        await ensure_batch_operator_access(context, world.bundle(), batch.id)
    assert exc_info.value.status_code == 403


async def test_ensure_batch_operator_access_denies_entity_staff(world) -> None:
    await _bootstrap(world)
    batch = await world.manual_extraction.create_batch("org-a", "B1")
    context = _context(_profile("u-ent", entity_id="entity-1"), {"can_process": True})
    with pytest.raises(HTTPException) as exc_info:
        await ensure_batch_operator_access(context, world.bundle(), batch.id)
    assert exc_info.value.status_code == 403


async def test_ensure_batch_operator_access_missing_batch(world) -> None:
    await _bootstrap(world)
    context = _context(_profile("u-op"), {"can_process": True})
    with pytest.raises(HTTPException) as exc_info:
        await ensure_batch_operator_access(context, world.bundle(), "batch-missing")
    assert exc_info.value.status_code == 404


async def test_ensure_entity_review_scope_internal_bypasses() -> None:
    await ensure_entity_review_scope(
        _context(_profile(entity_id=None)), None, _review(entity_id="entity-1")
    )


async def test_ensure_entity_review_scope_matches() -> None:
    await ensure_entity_review_scope(
        _context(_profile("u-ent", entity_id="entity-1")), None, _review(entity_id="entity-1")
    )


async def test_ensure_entity_review_scope_rejects_cross_entity() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await ensure_entity_review_scope(
            _context(_profile("u-ent", entity_id="entity-1")), None, _review(entity_id="entity-2")
        )
    assert exc_info.value.status_code == 403

# ---------------------------------------------------------------------------
# Pure guards
# ---------------------------------------------------------------------------


def test_ensure_staff_permission_allows() -> None:
    ensure_staff_permission(_context(_profile(), {"can_process": True}), "can_process")


def test_ensure_staff_permission_denies() -> None:
    with pytest.raises(HTTPException) as exc_info:
        ensure_staff_permission(_context(_profile(), {}), "can_process")
    assert exc_info.value.status_code == 403


def test_require_internal_staff_allows_internal() -> None:
    require_internal_staff(_context(_profile(entity_id=None)))


def test_require_internal_staff_denies_entity() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_internal_staff(_context(_profile(entity_id="entity-1")))
    assert exc_info.value.status_code == 403


def test_require_entity_scope_internal_bypasses() -> None:
    require_entity_scope(_context(_profile(entity_id=None)), "entity-1")


def test_require_entity_scope_matches() -> None:
    require_entity_scope(_context(_profile(entity_id="entity-1")), "entity-1")


def test_require_entity_scope_rejects_cross_entity() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_entity_scope(_context(_profile(entity_id="entity-1")), "entity-2")
    assert exc_info.value.status_code == 403


def test_require_entity_scope_requires_id() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_entity_scope(_context(_profile(entity_id=None)), "")
    assert exc_info.value.status_code == 422
