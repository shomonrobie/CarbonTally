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
    "can_extract, can_map, can_validate, can_calculate, "
    "can_confirm_automation, can_submit, "
    "client_access, invited_at, joined_at"
)

_CLIENT_COLUMNS = (
    "id, consultant_id, organization_id, client_name, client_industry, "
    "client_contact_email, client_contact_name, status, billing_plan, notes, "
    "created_by, created_at, suspended_at, ended_at, ended_by, "
    "lifecycle_updated_at, relationship_origin, engagement_requested_at, "
    "engagement_decided_by, engagement_decided_at"
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
        can_extract=bool(r.get("can_extract", False)),
        can_map=bool(r.get("can_map", False)),
        can_validate=bool(r.get("can_validate", False)),
        can_calculate=bool(r.get("can_calculate", False)),
        can_confirm_automation=bool(r.get("can_confirm_automation", False)),
        can_submit=bool(r.get("can_submit", False)),
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
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        relationship_origin=str(r["relationship_origin"]) if r.get("relationship_origin") else "consultant_created_customer",
        engagement_requested_at=r.get("engagement_requested_at"),
        engagement_decided_by=str(r["engagement_decided_by"]) if r.get("engagement_decided_by") else None,
        engagement_decided_at=r.get("engagement_decided_at"),
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

    async def get_profile_by_id(self, profile_id: str) -> Optional[ConsultantProfile]:
        """Return a consultant firm profile by its id (queue-disclosure context:
        an internal queue row can name the firm that manages the client org)."""
        row = await self._fetch_one(
            f"SELECT {_PROFILE_COLUMNS} FROM public.consultant_profiles "
            "WHERE id = $1 LIMIT 1",
            profile_id,
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

    async def get_user_summaries(self, user_ids: list[str]) -> dict[str, dict]:
        """Human-readable display info for team members (CL-61).

        Joins ``public.users`` (the app-side user table) so the team roster can
        show a name/email instead of raw UUIDs. Returns ``{user_id: {email,
        first_name, last_name}}`` for the requested ids.
        """
        if not user_ids:
            return {}
        placeholders = ", ".join(f"${i + 1}" for i in range(len(user_ids)))
        rows = await self._fetch_all(
            "SELECT id, email, first_name, last_name FROM public.users "
            f"WHERE id IN ({placeholders})",
            *user_ids,
        )
        return {
            str(r["id"]): {
                "email": r.get("email"),
                "first_name": r.get("first_name"),
                "last_name": r.get("last_name"),
            }
            for r in rows
        }

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

    async def get_active_memberships_by_user(self, user_id: str) -> list[ConsultantFirmMember]:
        """Every ACTIVE firm-membership row for a user (canonical Layer-2 query).

        This is the authoritative answer to "which Consultant firm(s) is this
        user an active member of?" and mirrors the RLS helper
        ``is_org_consultant`` (which resolves membership by ``user_id`` +
        ``is_active`` + the firm's client grants). Returns active rows only;
        inactive/revoked membership never resolves here.
        """
        rows = await self._fetch_all(
            f"SELECT {_MEMBER_COLUMNS} FROM public.consultant_firm_members "
            "WHERE user_id = $1 AND coalesce(is_active, true) = true "
            "ORDER BY created_at NULLS LAST",
            user_id,
        )
        return [_row_to_member(r) for r in rows]

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

    async def get_firm_member(self, firm_id: str, member_id: str) -> Optional[ConsultantFirmMember]:
        row = await self._fetch_one(
            f"SELECT {_MEMBER_COLUMNS} FROM public.consultant_firm_members "
            "WHERE firm_id = $1 AND id = $2 LIMIT 1",
            firm_id,
            member_id,
        )
        return _row_to_member(row) if row is not None else None

    async def set_firm_member_active(
        self, firm_id: str, member_id: str, is_active: bool
    ) -> Optional[ConsultantFirmMember]:
        """CL-61 close-out — revoke (deactivate) or reactivate a team member.

        Server-side enforcement: a deactivated member's permission flags no
        longer resolve at ``require_consultant`` (the member row is inactive),
        so access revocation is immediate and not merely a UI affordance.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.consultant_firm_members
            SET is_active = $3, updated_at = NOW()
            WHERE firm_id = $1 AND id = $2
            RETURNING {_MEMBER_COLUMNS}
            """,
            firm_id,
            member_id,
            is_active,
        )
        return _row_to_member(row) if row is not None else None

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
        if target_status not in (
            "active", "pending", "rejected", "suspended", "ended", "inactive"
        ):
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
                   engagement_decided_by = CASE WHEN $2 IN ('active', 'rejected')
                                                THEN $3 ELSE engagement_decided_by END,
                   engagement_decided_at = CASE WHEN $2 IN ('active', 'rejected')
                                                THEN NOW() ELSE engagement_decided_at END,
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

    async def list_engagements_for_org(
        self, organization_id: str, statuses: Optional[tuple[str, ...]] = None
    ) -> list[ConsultantClient]:
        """Consultant relationships targeting ``organization_id`` (customer side).

        Used by the customer engagement surface (P6-1C). Defaults to PENDING
        rows so the organisation can see requests awaiting its decision;
        other statuses may be listed explicitly for auditing.
        """
        statuses = statuses or ("pending",)
        rows = await self._fetch_all(
            f"SELECT {_CLIENT_COLUMNS} FROM public.consultant_clients "
            "WHERE organization_id = $1 AND status = ANY($2) "
            "ORDER BY created_at",
            organization_id,
            list(statuses),
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
        created_by: Optional[str] = None,
        relationship_origin: str = "consultant_created_customer",
        status: str = "active",
    ) -> ConsultantClient:
        """Insert a consultant↔organisation relationship row.

        ``relationship_origin`` distinguishes consultant-CREATED client
        organisations (Case A — active immediately via the approved
        provisioning flow) from ``engagement_request`` rows for ALREADY-existing
        organisations (Case B — inserted PENDING; only customer acceptance may
        move them to active). ``created_by`` is the authenticated actor.
        """
        if relationship_origin not in ("legacy", "consultant_created_customer", "engagement_request"):
            raise ValueError(f"unknown relationship_origin {relationship_origin!r}")
        if status not in ("active", "pending"):
            raise ValueError(f"new relationship status must be active or pending, got {status!r}")
        if relationship_origin == "engagement_request" and status != "pending":
            raise ValueError("engagement_request relationships must start PENDING (customer acceptance required)")
        requested = "NOW()" if status == "pending" else "NULL"
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_clients (
                consultant_id, organization_id, client_name, client_industry,
                client_contact_email, client_contact_name, status, created_by,
                relationship_origin, engagement_requested_at,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, {requested}, NOW(), NOW())
            RETURNING {_CLIENT_COLUMNS}
            """,
            consultant_id,
            organization_id,
            client_name,
            client_industry,
            client_contact_email,
            client_contact_name,
            status,
            created_by,
            relationship_origin,
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


