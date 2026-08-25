"""Operations staff domain objects (V3 Phase 8).

Immutable frozen dataclasses mirroring the V3M2 operations tables:
``staff_profiles`` and ``staff_roles``.

The CarbonTally-internal convention (ADR-V3-001 Q5, positive convention — NOT
unknown) is preserved: ``StaffProfile.entity_id IS NULL`` means the staff member
belongs to CarbonTally internal operations; a populated ``entity_id`` means the
staff member belongs to the referenced Processing Entity.

Authorization model (Phase 8):
    staff_profiles.user_id  → the auth.users identity
    staff_profiles.role_id  → ``roles.id`` (permissions resolved from the
                              ``roles.permissions`` jsonb, matching ``auth.py``)
    staff_profiles.entity_id → NULL = CarbonTally internal staff (ops-wide),
                               populated = processing-entity staff (entity scope)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

#: The documented permission vocabulary (``roles.permissions`` jsonb keys used by
#: ``auth.py`` ``DEFAULT_STAFF_PERMISSIONS``). Permission VALUES are read from the
#: real ``roles`` row — this tuple is only the reference vocabulary, not a matrix.
STAFF_PERMISSION_KEYS: tuple[str, ...] = (
    "can_view_all",
    "can_manage_staff",
    "can_manage_roles",
    "can_view_organizations",
    "can_manage_organizations",
    "can_extract",
    "can_process",
    "can_review",
    "can_approve",
    "can_export",
    "can_delete",
)

#: Permissions that gate the Phase 8 operational surfaces.
PERMISSION_DASHBOARD = "can_view_all"
PERMISSION_MANAGE_STAFF = "can_manage_staff"
PERMISSION_MANAGE_ROLES = "can_manage_roles"
PERMISSION_PROCESS = "can_process"
PERMISSION_REVIEW = "can_review"
PERMISSION_APPROVE = "can_approve"


@dataclass(frozen=True, slots=True)
class StaffProfile:
    """A staff profile row (``staff_profiles``).

    Attributes:
        id: Primary key (UUID string).
        user_id: The auth identity the profile belongs to.
        first_name / last_name: Display name.
        email: Contact email.
        role_id: Reference to ``roles.id`` (permissions source).
        is_active: Whether the profile is enabled.
        hire_date: Optional hire date.
        skills: Skills metadata (``skills`` jsonb).
        max_concurrent_tasks: Optional workload cap.
        entity_id: ``None`` = CarbonTally internal staff; populated = the
            Processing Entity the staff member belongs to.
    """

    id: str
    user_id: str
    first_name: str
    last_name: str
    email: str
    role_id: Optional[str] = None
    is_active: bool = True
    hire_date: Optional[date] = None
    skills: dict[str, Any] = field(default_factory=dict)
    max_concurrent_tasks: Optional[int] = None
    entity_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.user_id:
            raise ValueError("user_id must not be empty")
        if not self.first_name:
            raise ValueError("first_name must not be empty")
        if not self.last_name:
            raise ValueError("last_name must not be empty")
        if self.max_concurrent_tasks is not None and self.max_concurrent_tasks < 0:
            raise ValueError("max_concurrent_tasks must be >= 0")

    @property
    def is_internal_staff(self) -> bool:
        """``True`` when the staff member belongs to CarbonTally internal ops."""
        return self.entity_id is None


@dataclass(frozen=True, slots=True)
class StaffRole:
    """A staff-role definition row (``staff_roles``).

    The AUTHORITATIVE permission source for a staff member is
    ``staff_roles.permissions`` resolved via ``staff_profiles.role_id``
    (``staff_profiles.role_id`` is a foreign key to ``staff_roles.id``). The
    ``roles`` table is the customer-org role reference, not the staff model.
    """

    id: str
    name: str
    description: Optional[str] = None
    permissions: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
