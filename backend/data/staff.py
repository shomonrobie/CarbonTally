"""Operations staff repository (V3 Phase 8).

Persistence for the V3M2 operations surface: ``staff_profiles`` (the workforce
roster, including processing-entity staff via ``entity_id``) and ``staff_roles``
(the staff role reference catalog). Real-aggregate helpers power the operations
dashboard and the processing-entity dashboard.

No schema changes: every column referenced below exists in V3M2.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.staff import StaffProfile, StaffRole

_STAFF_COLUMNS = (
    "id, user_id, first_name, last_name, email, role_id, is_active, hire_date, "
    "skills, max_concurrent_tasks, entity_id, created_at, updated_at, "
    "created_by, updated_by"
)

_ROLE_COLUMNS = (
    "id, name, description, permissions, is_active, created_at, updated_at"
)


def _row_to_profile(row: Any) -> StaffProfile:
    r = dict(row)
    return StaffProfile(
        id=str(r["id"]),
        user_id=str(r["user_id"]),
        first_name=str(r["first_name"]),
        last_name=str(r["last_name"]),
        email=str(r["email"]),
        role_id=str(r["role_id"]) if r.get("role_id") else None,
        is_active=bool(r.get("is_active", True)),
        hire_date=r.get("hire_date"),
        skills=loads_jsonb(r.get("skills")) or {},
        max_concurrent_tasks=r.get("max_concurrent_tasks"),
        entity_id=str(r["entity_id"]) if r.get("entity_id") else None,
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        updated_by=str(r["updated_by"]) if r.get("updated_by") else None,
    )


def _row_to_role(row: Any) -> StaffRole:
    r = dict(row)
    return StaffRole(
        id=str(r["id"]),
        name=str(r["name"]),
        description=r.get("description"),
        permissions=loads_jsonb(r.get("permissions")) or {},
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )


class StaffRepository(AbstractRepository[StaffProfile]):
    """Staff roster + staff-role reference + real operations aggregates."""

    # -- staff profiles ------------------------------------------------------

    async def get_by_user(self, user_id: str) -> Optional[StaffProfile]:
        """Return the active-agnostic staff profile for ``user_id`` (or ``None``)."""
        row = await self._fetch_one(
            f"SELECT {_STAFF_COLUMNS} FROM public.staff_profiles WHERE user_id = $1",
            user_id,
        )
        return _row_to_profile(row) if row is not None else None

    async def get(self, id: str) -> Optional[StaffProfile]:
        """Return the profile with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_STAFF_COLUMNS} FROM public.staff_profiles WHERE id = $1",
            id,
        )
        return _row_to_profile(row) if row is not None else None

    async def list_profiles(self) -> list[StaffProfile]:
        """Return every staff profile, by name."""
        rows = await self._fetch_all(
            f"SELECT {_STAFF_COLUMNS} FROM public.staff_profiles "
            "ORDER BY first_name, last_name, id"
        )
        return [_row_to_profile(r) for r in rows]

    async def list_entity_staff(self, entity_id: str) -> list[StaffProfile]:
        """Return the staff belonging to one processing entity."""
        rows = await self._fetch_all(
            f"SELECT {_STAFF_COLUMNS} FROM public.staff_profiles "
            "WHERE entity_id = $1 ORDER BY first_name, last_name, id",
            entity_id,
        )
        return [_row_to_profile(r) for r in rows]

    async def create_profile(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
        email: str,
        role_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        max_concurrent_tasks: Optional[int] = None,
        created_by: Optional[str] = None,
    ) -> StaffProfile:
        """Insert a staff profile row and return it."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.staff_profiles (
                user_id, first_name, last_name, email, role_id, entity_id,
                max_concurrent_tasks, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
            RETURNING {_STAFF_COLUMNS}
            """,
            user_id,
            first_name,
            last_name,
            email,
            role_id,
            entity_id,
            max_concurrent_tasks,
            created_by,
        )
        if row is None:
            raise RuntimeError("staff_profiles insert returned no row")
        return _row_to_profile(row)

    async def update_profile(
        self,
        profile_id: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        role_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        max_concurrent_tasks: Optional[int] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[StaffProfile]:
        """Update the whitelisted real staff_profiles columns (``None`` = keep)."""
        sets, args = ["updated_at = NOW()"], [profile_id]
        mappings = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role_id": role_id,
            "entity_id": entity_id,
            "max_concurrent_tasks": max_concurrent_tasks,
            "is_active": is_active,
        }
        for column, value in mappings.items():
            if value is not None:
                args.append(value)
                sets.append(f"{column} = ${len(args)}")
        row = await self._fetch_one(
            f"UPDATE public.staff_profiles SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_STAFF_COLUMNS}",
            *args,
        )
        return _row_to_profile(row) if row is not None else None


    async def set_entity(
        self, profile_id: str, entity_id: Optional[str], updated_by: Optional[str] = None
    ) -> Optional[StaffProfile]:
        """Assign (or detach, ``entity_id=None``) a staff profile to an entity."""
        row = await self._fetch_one(
            f"""
            UPDATE public.staff_profiles
            SET entity_id = $2, updated_at = NOW(), updated_by = $3
            WHERE id = $1
            RETURNING {_STAFF_COLUMNS}
            """,
            profile_id,
            entity_id,
            updated_by,
        )
        return _row_to_profile(row) if row is not None else None

    async def save(self, entity: StaffProfile) -> StaffProfile:
        """Upsert a staff profile by id and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.staff_profiles (
                id, user_id, first_name, last_name, email, role_id, is_active,
                hire_date, skills, max_concurrent_tasks, entity_id, created_at,
                updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (id)
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                email = EXCLUDED.email,
                role_id = EXCLUDED.role_id,
                is_active = EXCLUDED.is_active,
                hire_date = EXCLUDED.hire_date,
                skills = EXCLUDED.skills,
                max_concurrent_tasks = EXCLUDED.max_concurrent_tasks,
                entity_id = EXCLUDED.entity_id,
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by
            RETURNING {_STAFF_COLUMNS}
            """,
            entity.id,
            entity.user_id,
            entity.first_name,
            entity.last_name,
            entity.email,
            entity.role_id,
            entity.is_active,
            entity.hire_date,
            dumps_jsonb(entity.skills),
            entity.max_concurrent_tasks,
            entity.entity_id,
            entity.created_at or None,
            entity.updated_at or None,
            entity.created_by,
            entity.updated_by,
        )
        if row is None:
            raise RuntimeError("staff_profiles upsert returned no row")
        return _row_to_profile(row)

    async def delete(self, id: str) -> None:
        """Staff profiles are never hard-deleted; deactivate via update_profile."""
        raise NotImplementedError(
            "staff_profiles are never hard-deleted; use update_profile(is_active=False)"
        )

    # -- staff roles (reference catalog) -------------------------------------

    async def get_role(self, role_id: str) -> Optional[StaffRole]:
        """Return the staff-role definition with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ROLE_COLUMNS} FROM public.staff_roles WHERE id = $1",
            role_id,
        )
        return _row_to_role(row) if row is not None else None

    async def list_roles(self) -> list[StaffRole]:
        """Return every staff-role definition, by name."""
        rows = await self._fetch_all(
            f"SELECT {_ROLE_COLUMNS} FROM public.staff_roles "
            "ORDER BY name, id"
        )
        return [_row_to_role(r) for r in rows]


    # -- real operations aggregates ------------------------------------------

    async def ops_dashboard(self) -> dict:
        """Global operations aggregates computed from the real tables.

        Counts are computed in SQL over the live rows (organizations,
        processing_entities, staff_profiles, manual_review_queue, issues). No
        fabricated statistics.
        """
        orgs = await self._fetch_all("SELECT COUNT(*) AS n FROM public.organizations")
        entities = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.processing_entities "
            "GROUP BY status ORDER BY status"
        )
        staff_by_scope = await self._fetch_all(
            "SELECT CASE WHEN entity_id IS NULL THEN 'internal' ELSE 'entity' END "
            "AS scope, COUNT(*) AS n FROM public.staff_profiles GROUP BY scope"
        )
        staff_by_entity = await self._fetch_all(
            "SELECT entity_id, COUNT(*) AS n FROM public.staff_profiles "
            "WHERE entity_id IS NOT NULL GROUP BY entity_id ORDER BY entity_id"
        )
        review_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_review_queue "
            "GROUP BY status ORDER BY status"
        )
        review_sla_breached = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.manual_review_queue "
            "WHERE sla_breached = TRUE"
        )
        issues_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.issues "
            "GROUP BY status ORDER BY status"
        )
        return {
            "organizations": {"total": int(orgs[0]["n"]) if orgs else 0},
            "entities": {
                "total": sum(int(r["n"]) for r in entities),
                "by_status": {str(r["status"]): int(r["n"]) for r in entities},
            },
            "staff": {
                "total": sum(int(r["n"]) for r in staff_by_scope),
                "internal": int(
                    next((int(r["n"]) for r in staff_by_scope if r["scope"] == "internal"), 0)
                ),
                "entity_staff": int(
                    next((int(r["n"]) for r in staff_by_scope if r["scope"] == "entity"), 0)
                ),
                "by_entity": {str(r["entity_id"]): int(r["n"]) for r in staff_by_entity},
            },
            "review_queue": {
                "total": sum(int(r["n"]) for r in review_by_status),
                "by_status": {str(r["status"]): int(r["n"]) for r in review_by_status},
                "sla_breached": int(review_sla_breached[0]["n"]) if review_sla_breached else 0,
            },
            "issues": {
                "total": sum(int(r["n"]) for r in issues_by_status),
                "by_status": {str(r["status"]): int(r["n"]) for r in issues_by_status},
            },
        }

    async def entity_dashboard(self, entity_id: str) -> dict:
        """Processing-entity dashboard aggregates over the real tables.

        Entity-scoped: ``manual_review_queue.entity_id`` and ``issues.entity_id``
        are the schema's entity links (ADR-V3-001 Q5). Manual-extraction
        batches/items have no entity column — they are never included here.
        """
        entity = await self._fetch_one(
            "SELECT id, name, status FROM public.processing_entities WHERE id = $1",
            entity_id,
        )
        if entity is None:
            raise RuntimeError(f"processing entity {entity_id!r} does not exist")
        review_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.manual_review_queue "
            "WHERE entity_id = $1 GROUP BY status ORDER BY status",
            entity_id,
        )
        review_sla = await self._fetch_all(
            "SELECT COUNT(*) AS n FROM public.manual_review_queue "
            "WHERE entity_id = $1 AND sla_breached = TRUE",
            entity_id,
        )
        issues_by_status = await self._fetch_all(
            "SELECT status, COUNT(*) AS n FROM public.issues "
            "WHERE entity_id = $1 GROUP BY status ORDER BY status",
            entity_id,
        )
        staff = await self.list_entity_staff(entity_id)
        return {
            "entity": {
                "id": str(entity["id"]),
                "name": str(entity["name"]),
                "status": str(entity["status"]),
            },
            "staff_count": len(staff),
            "review_queue": {
                "total": sum(int(r["n"]) for r in review_by_status),
                "by_status": {str(r["status"]): int(r["n"]) for r in review_by_status},
                "sla_breached": int(review_sla[0]["n"]) if review_sla else 0,
            },
            "issues": {
                "total": sum(int(r["n"]) for r in issues_by_status),
                "by_status": {str(r["status"]): int(r["n"]) for r in issues_by_status},
            },
        }

