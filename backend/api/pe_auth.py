"""Processing Entity authorization (Phase 3 / PE-ROLE-001).

Every ``/api/v3/pe/*`` endpoint resolves the caller through this module:

    authenticated identity
        → active staff profile with a Processing Entity (``entity_id`` set)
        → ACTIVE Processing Entity
        → stored staff role key → frozen PE-role vocabulary (PE-ROLE-001)
        → entity-scoped capability set

The stored staff-role vocabulary (``staff_roles.name``: ``operator``,
``reviewer``, ``qc_specialist``, ``pe_manager``) is the LEGACY representation
that must remain compatible while the canonical model moves toward the frozen
vocabulary. This module performs that mapping in code — no database migration,
no deleted memberships, no deleted PE relationships:

    Data Entry Operator  ←  ``operator``
    Reviewer             ←  ``reviewer``
    QC Specialist        ←  ``qc_specialist``
    Admin                ←  ``pe_manager``

PE roles are entity-membership scoped and never grant Customer, Consultant,
CarbonTally Operations or CarbonTally Admin privileges. CarbonTally INTERNAL
staff (``entity_id IS NULL``) belong to ``/ops`` and are denied on ``/pe``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException

from api.dependencies import RepositoryBundle, get_repositories
from api.operations_auth import StaffContext, require_staff
from auth import AuthUser, get_current_user

#: Stored staff-role key → frozen PE role label (PE-ROLE-001).
PE_FROZEN_ROLE_LABELS: dict[str, str] = {
    "operator": "Data Entry Operator",
    "reviewer": "Reviewer",
    "qc_specialist": "QC Specialist",
    "pe_manager": "Admin",
}

#: Capability surface. Actions are additionally enforced by the shared
#: operations handlers (staff-role ``permissions``) — this is the PE-domain
#: policy layer, not the only one.
#
#: Capability matrix (frozen PE-ROLE-001 + approved V1.2 design Part 1):
#:   operator      (Data Entry Operator) → read_work, process, communicate
#:   reviewer      (Reviewer)            → read_work, review, communicate
#:   qc_specialist (QC Specialist)       → read_work, qc, communicate
#:   pe_manager    (Admin)               → read_work, process, review, qc,
#:                                          communicate, manage_team
#: Admin intentionally retains the full PE-domain capability set: the PE Admin
#: is the administrative operator of the Processing Entity and may perform any
#: PE-domain operational action (staff-role ``pe_manager`` already grants
#: ``can_process``/``can_review`` on the shared row). This is a PE-trust-domain
#: capability and NEVER grants Customer/Consultant/CarbonTally Operations/
#: CarbonTally Admin authority (see the authorization trust-domain checks).
#: Because the role is authorized, an Admin request against a work item in an
#: invalid workflow state correctly returns 409 (workflow-state error), not 403.
PE_ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    "operator": frozenset({"read_work", "process", "communicate"}),
    "reviewer": frozenset({"read_work", "review", "communicate"}),
    "qc_specialist": frozenset({"read_work", "qc", "communicate"}),
    "pe_manager": frozenset(
        {"read_work", "process", "review", "qc", "communicate", "manage_team"}
    ),
}

#: Capabilities required for each workflow action exposed on the PE contract.
CAP_READ_WORK = "read_work"
CAP_PROCESS = "process"
CAP_REVIEW = "review"
CAP_QC = "qc"
CAP_COMMUNICATE = "communicate"
CAP_MANAGE_TEAM = "manage_team"


@dataclass(frozen=True, slots=True)
class PEContext:
    """The authenticated PE member's entity-scoped context."""

    entity_id: str
    entity: Any
    staff: StaffContext
    role_key: str
    role_label: str
    capabilities: frozenset[str]

    @property
    def user_id(self) -> str:
        """The member's user id (from the active staff profile)."""
        return self.staff.profile.user_id

    def can(self, capability: str) -> bool:
        """Whether the member's frozen PE role grants ``capability``."""
        return capability in self.capabilities


async def _resolve_pe_context(
    current_user: Optional[AuthUser],
    repos: RepositoryBundle,
) -> Optional[PEContext]:
    if current_user is None:
        return None
    ctx: Optional[StaffContext] = None
    try:
        ctx = await require_staff(current_user=current_user, repos=repos)
    except HTTPException:
        return None
    profile = ctx.profile
    entity_id = profile.entity_id
    if not entity_id:
        # CarbonTally internal staff use /ops — they are not PE members.
        return None
    entity = await repos.entities.get(entity_id)
    if entity is None:
        return None
    if entity.status != "active":
        # Suspended/remediation/terminated entities cannot process work.
        return None
    role_key = ""
    if profile.role_id:
        role = await repos.staff.get_role(profile.role_id)
        if role is not None:
            role_key = str(role.name or "")
    label = PE_FROZEN_ROLE_LABELS.get(role_key)
    capabilities = PE_ROLE_CAPABILITIES.get(role_key)
    if label is None or capabilities is None:
        # An entity staff member with a non-PE staff role cannot use /pe.
        return None
    return PEContext(
        entity_id=entity_id,
        entity=entity,
        staff=ctx,
        role_key=role_key,
        role_label=label,
        capabilities=capabilities,
    )


async def require_pe_member(
    current_user: Optional[AuthUser] = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> PEContext:
    """Dependency: an ACTIVE Processing Entity member (own-entity scope)."""
    context = await _resolve_pe_context(current_user, repos)
    if context is None:
        raise HTTPException(
            status_code=403,
            detail="Processing Entity access required (active PE membership)",
        )
    return context


def require_pe_capability(capability: str):
    """Dependency factory: deny when the member's PE role lacks ``capability``."""

    async def checker(
        pe: PEContext = Depends(require_pe_member),
    ) -> PEContext:
        if not pe.can(capability):
            raise HTTPException(
                status_code=403,
                detail=f"Your PE role ({pe.role_label}) does not allow this action",
            )
        return pe

    return checker
