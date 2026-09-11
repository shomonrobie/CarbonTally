"""Deterministic demo runtime context (org / entity / user ids).

The investor-demo seeder provisions every demo record with a deterministic
UUID: ``uuid5(NAMESPACE_URL, "carbontally-demo:" + seed_key)`` (verified
against the live local database — org/user/entity ids match exactly). This
module exposes that scheme so the run layer can resolve an identity to its
organisation / processing entity / staff ids WITHOUT touching the database.
The DB layer still validates that the resolved ids exist (read-only).

Seed keys (from tools/seed_investor_demo):

* ``org:{i}``            — direct customer organisation 1..50
* ``client_org:{ci}:{k}`` — consultant client organisation (firm ci, client k)
* ``user:{org}:{role}``  — direct customer user (owner/admin/member/viewer)
* ``entity:{i}``         — processing entity 1..3 (Alpha/Beta/Gamma)
* ``staff_user:{key}``   — staff / PE user (operator, reviewer, qc,
                            staff-admin, system-admin, pe-manager-{i}, pe-staff-{i})
"""

from __future__ import annotations

import uuid
from typing import Dict, Optional

NAMESPACE = uuid.NAMESPACE_URL
PREFIX = "carbontally-demo:"

# Direct customer organisations (org_index 1..50).
CUSTOMER_ORG_COUNT = 50
# Processing entities (Alpha=1, Beta=2, Gamma=3).
PE_ENTITY_COUNT = 3

# Staff user seed keys (from seed_core.staff_spec).
INTERNAL_STAFF_KEYS = ("operator", "reviewer", "qc", "staff-admin", "system-admin")
PE_STAFF_PREFIXES = ("pe-manager", "pe-staff")


def demo_uuid(seed_key: str) -> str:
    """Deterministic demo UUID for a seed key."""
    return str(uuid.uuid5(NAMESPACE, PREFIX + seed_key))


def organization_id(org_index: int) -> str:
    """Direct customer organisation id for org_index 1..50."""
    return demo_uuid(f"org:{org_index}")


def client_organization_id(consultant_index: int, client_number: int) -> str:
    """Consultant client organisation id (firm + client number)."""
    return demo_uuid(f"client_org:{consultant_index}:{client_number}")


def user_id(org_index: int, role: str) -> str:
    """Direct customer user id (role in owner/admin/member/viewer)."""
    return demo_uuid(f"user:{org_index}:{role}")


def entity_id(entity_index: int) -> str:
    """Processing entity id (1..3)."""
    return demo_uuid(f"entity:{entity_index}")


def staff_user_id(key: str) -> str:
    """Staff / PE user id for a staff seed key."""
    return demo_uuid(f"staff_user:{key}")


def staff_profile_id(key: str) -> str:
    """Staff profile id for a staff seed key."""
    return demo_uuid(f"staff_profile:{key}")


def client_owner_user_id(consultant_index: int, client_number: int) -> str:
    """Client-owner user id (consultant client)."""
    return demo_uuid(f"client_user:{consultant_index}:{client_number}")


def resolve_context(persona: str, *, org_index: int = 0,
                    consultant_index: int = 0, client_number: int = 0,
                    entity_index: int = 0, staff_key: str = "") -> Dict[str, object]:
    """Return the deterministic runtime context for a persona.

    Personas handled: owner/admin/member/viewer, client_owner, consultant,
    pe_manager/pe_staff, operator/reviewer/qc/staff-admin/system-admin,
    legacy/audit/fixture (no runtime context).
    """
    context: Dict[str, object] = {}
    if persona in ("owner", "admin", "member", "viewer"):
        context["organization_id"] = organization_id(org_index)
        context["member_role"] = "owner" if persona == "owner" else persona
    elif persona == "client_owner":
        context["organization_id"] = client_organization_id(consultant_index, client_number)
        context["member_role"] = "owner"
    elif persona == "consultant":
        context["consultant_index"] = consultant_index
    elif persona in ("pe_manager", "pe_staff"):
        context["processing_entity_id"] = entity_id(entity_index)
        context["is_pe"] = True
        context["is_staff"] = True
    elif persona in ("operator", "reviewer", "qc", "staff-admin", "staff_admin",
                     "system-admin", "system_admin"):
        context["is_staff"] = True
        context["staff_role"] = {
            "operator": "operator",
            "reviewer": "reviewer",
            "qc": "qc",
            "staff-admin": "staff_admin",
            "staff_admin": "staff_admin",
            "system-admin": "system_admin",
            "system_admin": "system_admin",
        }[persona]
    return context
