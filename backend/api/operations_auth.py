"""V3 operations authorization (Phase 8).

The CarbonTally-internal workforce authorization chain, implemented server-side
over the REAL schema tables (no invented roles/permissions):

    authenticated user
        → staff profile (``staff_profiles``, active)
        → permissions (``staff_roles.permissions`` jsonb resolved via
          ``staff_profiles.role_id`` — the authoritative staff-role table)
        → scope (``staff_profiles.entity_id``:
            NULL       = CarbonTally internal staff → ops-wide surfaces
            populated  = processing-entity staff → entity-scoped surfaces only)

Every /api/v3/ops/* endpoint passes ``require_staff()`` (or
``require_internal_staff()``) and then re-authorizes every item/batch/entity the
caller touches. The browser-supplied ids are never trusted without these checks.

Entity isolation rules (P0):
* Processing-entity staff can ONLY touch work linked to their own entity
  (``manual_review_queue.entity_id`` / ``issues.entity_id``). Manual-extraction
  batches/items have NO entity column in the schema, so entity staff are
  structurally unable to access the manual-extraction pipeline.
* CarbonTally internal staff (``entity_id IS NULL``) are the only identities
  that can run the manual-extraction pipeline and the ops-wide dashboard.
* An operator (``can_process``) may only touch items in batches assigned to them
  (or unassigned open batches — the schema's self-serve queue model).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from domain.staff import StaffProfile


@dataclass(frozen=True, slots=True)
class StaffContext:
    """The authenticated staff member's identity + real permissions."""

    profile: StaffProfile
    permissions: dict[str, Any]


async def _resolve_context(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[StaffContext]:
    profile = await repos.staff.get_by_user(current_user.user_id)
    if profile is None or not profile.is_active:
        return None
    permissions: dict[str, Any] = {}
    if profile.role_id:
        # Authoritative staff permission source: `staff_profiles.role_id`
        # references `staff_roles` (the schema's staff-role vocabulary). The
        # `roles` table is the customer-org role reference and is NOT the
        # staff permission source.
        role = await repos.staff.get_role(profile.role_id)
        if role is not None and role.permissions:
            permissions = dict(role.permissions)
    return StaffContext(profile=profile, permissions=permissions)


async def require_staff(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> StaffContext:
    """Dependency: the caller must be an active staff profile."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(
            status_code=403,
            detail="Staff access required (active staff profile)",
        )
    return context


def ensure_staff_permission(context: StaffContext, permission: str) -> None:
    """Reject an action the staff role's real ``roles.permissions`` do not allow."""
    if not context.permissions.get(permission, False):
        raise HTTPException(
            status_code=403,
            detail=f"staff lacks permission: {permission}",
        )


def require_internal_staff(context: StaffContext) -> None:
    """Reject processing-entity staff from ops-wide/CarbonTally surfaces.

    ``staff_profiles.entity_id IS NULL`` is the positive convention for
    CarbonTally internal processing staff (ADR-V3-001 Q5).
    """
    if context.profile.entity_id is not None:
        raise HTTPException(
            status_code=403,
            detail="CarbonTally internal staff access required",
        )


def require_entity_scope(context: StaffContext, entity_id: str) -> None:
    """Entity isolation: entity staff may only touch their own entity."""
    if not entity_id:
        raise HTTPException(status_code=422, detail="entity_id is required")
    if (
        context.profile.entity_id is not None
        and context.profile.entity_id != entity_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Staff member is not authorized for this processing entity",
        )


async def ensure_batch_operator_access(
    context: StaffContext,
    repos: RepositoryBundle,
    batch_id: str,
) -> "Any":
    """Authorize an internal operator to touch items in ``batch_id``.

    D22: manual-extraction batches now carry an optional ``entity_id``
    (Processing Entity assignment). A batch has exactly ONE processing party:

    * Entity staff (``entity_id`` populated): may touch ONLY batches assigned
      to their own entity (``batch.entity_id == profile.entity_id``).
    * Internal staff (``entity_id IS NULL``): may touch only CarbonTally-
      internal batches (``batch.entity_id IS NULL``) assigned to them or
      open/unassigned (the self-serve queue model). Entity-assigned batches are
      the entity's work — reassignment is the explicit return path.
    """
    from domain.partners import ManualExtractionBatch

    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    if context.profile.entity_id is not None:
        if batch.entity_id != context.profile.entity_id:
            raise HTTPException(
                status_code=403,
                detail="Batch is not assigned to this processing entity",
            )
        return batch
    if batch.entity_id is not None:
        raise HTTPException(
            status_code=403,
            detail="Batch is assigned to a processing entity; reassign to internal staff first",
        )
    if batch.assigned_to not in (None, context.profile.user_id):
        raise HTTPException(
            status_code=403,
            detail="Operator is not assigned to this batch",
        )
    return batch


async def ensure_entity_batch_access(
    context: StaffContext,
    repos: RepositoryBundle,
    entity_id: str,
    batch_id: str,
) -> "Any":
    """Authorize the caller to touch one extraction batch inside a workspace.

    The batch must be assigned to the requested Processing Entity
    (``batch.entity_id == entity_id``). Entity staff additionally must belong
    to that entity (own-entity scope is enforced by ``require_entity_scope``);
    internal staff may read any batch but still through the requested
    workspace's scope.
    """
    batch = await repos.manual_extraction.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    if batch.entity_id != entity_id:
        raise HTTPException(
            status_code=403,
            detail="Batch is not assigned to the requested processing entity",
        )
    return batch


async def ensure_entity_review_scope(
    context: StaffContext,
    repos: RepositoryBundle,
    review: "Any",
) -> None:
    """Authorize the caller to touch one review-queue item.

    Entity staff must belong to the item's entity; CarbonTally internal staff
    may review (schema: ``manual_review_queue.entity_id``).
    """
    if context.profile.entity_id is not None:
        if review.entity_id != context.profile.entity_id:
            raise HTTPException(
                status_code=403,
                detail="Review item does not belong to this processing entity",
            )
