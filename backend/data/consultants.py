"""Consultants repository (V3 new capability).

Persistence for the consultant surface: ``consultant_profiles``,
``consultant_firm_members``, ``consultant_clients`` and ``consultant_tasks``.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.branding import ConsultantBranding
from domain.partners import (
    ConsultantClient,
    ConsultantFirmMember,
    ConsultantProfile,
    ConsultantTask,
)

_PROFILE_COLUMNS = (
    "id, user_id, company_name, brand_name, email_from, website, phone, "
    "country, vat_number, partner_status, is_active, created_at"
)

#: D21 branding projection of the profile row (the source of truth).
_BRANDING_COLUMNS = (
    "id AS profile_id, brand_name, logo_url, primary_color, secondary_color, "
    "footer_text, email_from, website, support_email, support_phone, "
    "support_hours, client_portal_url, white_label_enabled, co_branding_enabled"
)

#: The only columns the D21 branding self-service may write (partner_*,
#: commission_rate and api_key/webhook_url stay CarbonTally-controlled).
_BRANDING_UPDATE_COLUMNS: dict[str, str] = {
    "brand_name": "brand_name",
    "logo_url": "logo_url",
    "primary_color": "primary_color",
    "secondary_color": "secondary_color",
    "footer_text": "footer_text",
    "email_from": "email_from",
    "website": "website",
    "support_email": "support_email",
    "support_phone": "support_phone",
    "support_hours": "support_hours",
    "client_portal_url": "client_portal_url",
    "white_label_enabled": "white_label_enabled",
    "co_branding_enabled": "co_branding_enabled",
}

_MEMBER_COLUMNS = (
    "id, firm_id, user_id, role, is_active, can_manage_clients, "
    "can_upload_documents, can_generate_reports, can_manage_team, "
    "client_access, invited_at, joined_at"
)

_CLIENT_COLUMNS = (
    "id, consultant_id, organization_id, client_name, client_industry, "
    "client_contact_email, client_contact_name, status, billing_plan, notes, "
    "created_at, suspended_at, ended_at, ended_by, lifecycle_updated_at"
)

_TASK_COLUMNS = (
    "id, consultant_id, task_title, client_id, task_type, priority, status, "
    "assigned_to, due_date, completed_at, metadata, created_at"
)


def _row_to_branding(row: Any) -> ConsultantBranding:
    r = dict(row)
    return ConsultantBranding(
        profile_id=str(r["profile_id"]),
        brand_name=r.get("brand_name"),
        logo_url=r.get("logo_url"),
        primary_color=r.get("primary_color"),
        secondary_color=r.get("secondary_color"),
        footer_text=r.get("footer_text"),
        email_from=r.get("email_from"),
        website=r.get("website"),
        support_email=r.get("support_email"),
        support_phone=r.get("support_phone"),
        support_hours=r.get("support_hours"),
        client_portal_url=r.get("client_portal_url"),
        white_label_enabled=bool(r.get("white_label_enabled", False)),
        co_branding_enabled=bool(r.get("co_branding_enabled", False)),
    )


def _row_to_profile(row: Any) -> ConsultantProfile:
    r = dict(row)
    return ConsultantProfile(
        id=str(r["id"]),
        user_id=str(r["user_id"]),
        company_name=str(r["company_name"]),
        brand_name=r.get("brand_name"),
        email_from=r.get("email_from"),
        website=r.get("website"),
        phone=r.get("phone"),
        country=r.get("country"),
        vat_number=r.get("vat_number"),
        partner_status=r.get("partner_status"),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
    )


def _row_to_member(row: Any) -> ConsultantFirmMember:
    r = dict(row)
    return ConsultantFirmMember(
        id=str(r["id"]),
        firm_id=str(r["firm_id"]),
        user_id=str(r["user_id"]),
        role=str(r["role"]),
        is_active=bool(r.get("is_active", True)),
        can_manage_clients=bool(r.get("can_manage_clients", False)),
        can_upload_documents=bool(r.get("can_upload_documents", False)),
        can_generate_reports=bool(r.get("can_generate_reports", False)),
        can_manage_team=bool(r.get("can_manage_team", False)),
        client_access=list(r.get("client_access") or []),
        invited_at=r.get("invited_at"),
        joined_at=r.get("joined_at"),
    )


def _row_to_client(row: Any) -> ConsultantClient:
    r = dict(row)
    return ConsultantClient(
        id=str(r["id"]),
        consultant_id=str(r["consultant_id"]),
        organization_id=str(r["organization_id"]),
        client_name=str(r["client_name"]),
        client_industry=r.get("client_industry"),
        client_contact_email=r.get("client_contact_email"),
        client_contact_name=r.get("client_contact_name"),
        status=r.get("status"),
        billing_plan=r.get("billing_plan"),
        notes=r.get("notes"),
        created_at=r.get("created_at"),
        suspended_at=r.get("suspended_at"),
        ended_at=r.get("ended_at"),
        ended_by=str(r["ended_by"]) if r.get("ended_by") else None,
        lifecycle_updated_at=r.get("lifecycle_updated_at"),
    )


def _row_to_task(row: Any) -> ConsultantTask:
    r = dict(row)
    return ConsultantTask(
        id=str(r["id"]),
        consultant_id=str(r["consultant_id"]),
        task_title=str(r["task_title"]),
        client_id=r.get("client_id"),
        task_type=r.get("task_type"),
        priority=r.get("priority"),
        status=r.get("status"),
        assigned_to=r.get("assigned_to"),
        due_date=r.get("due_date"),
        completed_at=r.get("completed_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
        created_at=r.get("created_at"),
    )


class ConsultantsRepository(AbstractRepository[dict]):
    """Consultant profiles, firm members, client grants and tasks."""

    # -- profiles ----------------------------------------------------------
    async def get_profile_by_user(self, user_id: str) -> Optional[ConsultantProfile]:
        row = await self._fetch_one(
            f"SELECT {_PROFILE_COLUMNS} FROM public.consultant_profiles "
            "WHERE user_id = $1 LIMIT 1",
            user_id,
        )
        return _row_to_profile(row) if row is not None else None

    async def create_profile(self, user_id: str, company_name: str) -> ConsultantProfile:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_profiles (user_id, company_name, is_active, created_at, updated_at)
            VALUES ($1, $2, TRUE, NOW(), NOW())
            RETURNING {_PROFILE_COLUMNS}
            """,
            user_id,
            company_name,
        )
        if row is None:
            raise RuntimeError("consultant_profiles insert returned no row")
        return _row_to_profile(row)

    # -- branding (D21 white-label foundation) ------------------------------
    async def get_branding(self, profile_id: str) -> Optional[ConsultantBranding]:
        """Return the firm's branding projection of its own profile row."""
        row = await self._fetch_one(
            f"SELECT {_BRANDING_COLUMNS} FROM public.consultant_profiles "
            "WHERE id = $1",
            profile_id,
        )
        return _row_to_branding(row) if row is not None else None

    async def update_branding(
        self, profile_id: str, fields: dict[str, Any]
    ) -> Optional[ConsultantBranding]:
        """Update branding columns on the firm's own profile row.

        ``profile_id`` MUST be the caller's own profile id resolved from the
        authenticated consultant context (never a client-supplied value — the
        D21.14 ownership rule). Only the allowlisted branding columns are ever
        written; ``partner_*`` / ``commission_rate`` stay CarbonTally-only.
        """
        pairs: list[str] = []
        values: list[Any] = [profile_id]
        for key, column in _BRANDING_UPDATE_COLUMNS.items():
            if key in fields:
                pairs.append(f"{column} = ${len(values) + 1}")
                values.append(fields[key])
        if not pairs:
            return await self.get_branding(profile_id)
        pairs.append("updated_at = NOW()")
        query = (
            f"UPDATE public.consultant_profiles SET {', '.join(pairs)} "
            f"WHERE id = $1 RETURNING {_BRANDING_COLUMNS}"
        )
        row = await self._fetch_one(query, *values)
        return _row_to_branding(row) if row is not None else None

    # -- firm members ------------------------------------------------------
    async def list_firm_members(self, firm_id: str) -> list[ConsultantFirmMember]:
        rows = await self._fetch_all(
            f"SELECT {_MEMBER_COLUMNS} FROM public.consultant_firm_members "
            "WHERE firm_id = $1 ORDER BY joined_at NULLS LAST, created_at",
            firm_id,
        )
        return [_row_to_member(r) for r in rows]

    async def get_firm_member_by_user(
        self, firm_id: str, user_id: str
    ) -> Optional[ConsultantFirmMember]:
        row = await self._fetch_one(
            f"SELECT {_MEMBER_COLUMNS} FROM public.consultant_firm_members "
            "WHERE firm_id = $1 AND user_id = $2 LIMIT 1",
            firm_id,
            user_id,
        )
        return _row_to_member(row) if row is not None else None

    async def add_firm_member(self, firm_id: str, user_id: str, role: str) -> ConsultantFirmMember:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_firm_members (firm_id, user_id, role, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, TRUE, NOW(), NOW())
            RETURNING {_MEMBER_COLUMNS}
            """,
            firm_id,
            user_id,
            role,
        )
        if row is None:
            raise RuntimeError("consultant_firm_members insert returned no row")
        return _row_to_member(row)

    # -- clients -----------------------------------------------------------
    async def list_clients(self, consultant_id: str) -> list[ConsultantClient]:
        rows = await self._fetch_all(
            f"SELECT {_CLIENT_COLUMNS} FROM public.consultant_clients "
            "WHERE consultant_id = $1 ORDER BY client_name",
            consultant_id,
        )
        return [_row_to_client(r) for r in rows]

    async def get_client_by_org(
        self, consultant_id: str, organization_id: str
    ) -> Optional[ConsultantClient]:
        """Return the firm→organisation grant row (the relationship model)."""
        row = await self._fetch_one(
            f"SELECT {_CLIENT_COLUMNS} FROM public.consultant_clients "
            "WHERE consultant_id = $1 AND organization_id = $2 LIMIT 1",
            consultant_id,
            organization_id,
        )
        return _row_to_client(row) if row is not None else None

    async def update_client_status(
        self, client_id: str, status: str
    ) -> Optional[ConsultantClient]:
        """Legacy status write (kept for backward compatibility). Prefer
        :meth:`transition_client_lifecycle` for D19 lifecycle moves."""
        return await self.transition_client_lifecycle(client_id, status, actor_id=None)

    async def transition_client_lifecycle(
        self,
        client_id: str,
        target_status: str,
        *,
        actor_id: Optional[str] = None,
    ) -> Optional[ConsultantClient]:
        """Transition a client relationship to ``target_status``.

        Lifecycle vocabulary (D19 Part 4): ``active`` / ``suspended`` /
        ``ended`` (plus legacy ``inactive``). Timestamps are maintained so the
        lifecycle is auditable and the API/RLS continue to gate access on
        ``status = 'active'`` (D15). ``actor_id`` records who performed the
        transition (provenance, not authorization).
        """
        if target_status not in ("active", "suspended", "ended", "inactive"):
            raise ValueError(f"unknown client lifecycle status {target_status!r}")
        row = await self._fetch_one(
            f"""
            UPDATE public.consultant_clients
               SET status = $2,
                   suspended_at = CASE WHEN $2 = 'suspended' THEN NOW()
                                       ELSE suspended_at END,
                   ended_at = CASE WHEN $2 = 'ended' THEN NOW()
                                   ELSE ended_at END,
                   ended_by = CASE WHEN $2 = 'ended' THEN $3
                                   ELSE ended_by END,
                   lifecycle_updated_at = NOW(),
                   updated_at = NOW()
             WHERE id = $1
            RETURNING {_CLIENT_COLUMNS}
            """,
            client_id,
            target_status,
            actor_id,
        )
        return _row_to_client(row) if row is not None else None

    async def list_active_client_grants(self, organization_id: str) -> list[ConsultantClient]:
        """Every ACTIVE consultant grant for an organisation (used to end
        consultant access when the customer becomes a Direct Customer)."""
        rows = await self._fetch_all(
            f"SELECT {_CLIENT_COLUMNS} FROM public.consultant_clients "
            "WHERE organization_id = $1 AND status = 'active'",
            organization_id,
        )
        return [_row_to_client(r) for r in rows]

    async def add_client(
        self,
        consultant_id: str,
        organization_id: str,
        client_name: str,
        client_industry: Optional[str],
        client_contact_email: Optional[str],
        client_contact_name: Optional[str],
    ) -> ConsultantClient:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_clients (
                consultant_id, organization_id, client_name, client_industry,
                client_contact_email, client_contact_name, status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, 'active', NOW(), NOW())
            RETURNING {_CLIENT_COLUMNS}
            """,
            consultant_id,
            organization_id,
            client_name,
            client_industry,
            client_contact_email,
            client_contact_name,
        )
        if row is None:
            raise RuntimeError("consultant_clients insert returned no row")
        return _row_to_client(row)

    async def get_client(self, client_id: str) -> Optional[ConsultantClient]:
        row = await self._fetch_one(
            f"SELECT {_CLIENT_COLUMNS} FROM public.consultant_clients WHERE id = $1",
            client_id,
        )
        return _row_to_client(row) if row is not None else None

    # -- tasks -------------------------------------------------------------
    async def list_tasks(self, consultant_id: str, status: Optional[str] = None) -> list[ConsultantTask]:
        query = (
            f"SELECT {_TASK_COLUMNS} FROM public.consultant_tasks "
            "WHERE consultant_id = $1"
        )
        if status is not None:
            query += " AND status = $2"
            rows = await self._fetch_all(query + " ORDER BY created_at DESC", consultant_id, status)
        else:
            rows = await self._fetch_all(query + " ORDER BY created_at DESC", consultant_id)
        return [_row_to_task(r) for r in rows]

    async def create_task(
        self,
        consultant_id: str,
        task_title: str,
        task_type: Optional[str],
        priority: Optional[str],
        client_id: Optional[str],
        metadata: Optional[dict],
    ) -> ConsultantTask:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_tasks (
                consultant_id, task_title, task_type, priority, status, client_id,
                metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, 'open', $5, $6, NOW(), NOW())
            RETURNING {_TASK_COLUMNS}
            """,
            consultant_id,
            task_title,
            task_type,
            priority,
            client_id,
            dumps_jsonb(metadata or {}),
        )
        if row is None:
            raise RuntimeError("consultant_tasks insert returned no row")
        return _row_to_task(row)

    async def update_task_status(self, task_id: str, status: str) -> Optional[ConsultantTask]:
        row = await self._fetch_one(
            f"""
            UPDATE public.consultant_tasks
            SET status = $2,
                completed_at = CASE WHEN $2 = 'completed' THEN NOW() ELSE completed_at END,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_TASK_COLUMNS}
            """,
            task_id,
            status,
        )
        return _row_to_task(row) if row is not None else None

    async def get(self, id: str):
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None


