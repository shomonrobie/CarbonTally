"""Organisations repository (Backend v2.1 §10).

Persistence for the RC2 ``organizations`` aggregate and its child structures
(members, metadata, facilities, assets).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, loads_jsonb
from domain.organization import (
    Asset,
    Facility,
    Organization,
    OrganizationMember,
    OrganizationMetadata,
)

_ORG_COLUMNS = "id, name, country, is_active, created_at, billing_mode"

#: Full ``organizations`` row (customer profile + settings surface). Column
#: list mirrors the V3M2 schema exactly — no invented fields.
_ORG_FULL_COLUMNS = """
    id, name, company_number, created_at, updated_at, logo_url, industry,
    sector, company_size, vat_number, registration_number, registered_address,
    country, timezone, currency, financial_year_end, reporting_standard,
    secr_enabled, esrs_enabled, issb_enabled, default_factor_year,
    preferred_units, website, primary_contact_email, primary_contact_name,
    billing_contact_email, billing_contact_name, subscription_status,
    subscription_tier, billing_address, tax_rate, metadata,
    address_line1, address_line2, city, county, postcode, eircode, language,
    locale, vat_region, vat_registered, tax_region, registration_region,
    sic_code, naics_code, nace_code, business_structure, is_public, is_listed,
    reporting_frequency, accounting_standard, sustainability_standard,
    carbon_tax_region, data_protection_officer, privacy_policy_url, terms_url,
    is_active
"""

_MEMBER_COLUMNS = "id, organization_id, user_id, role, is_active, created_at"

_MEMBER_EMAIL_COLUMNS = (
    "m.id, m.organization_id, m.user_id, m.role, m.is_active, m.created_at, "
    "u.email AS user_email, u.first_name AS user_first_name, "
    "u.last_name AS user_last_name"
)

_METADATA_COLUMNS = """
    total_floor_area_sqm, occupied_floor_area_sqm, average_employees,
    annual_revenue, industry_sector
"""

#: Full ``organization_metadata`` row (mirrors the V3M2 schema).
_METADATA_FULL_COLUMNS = """
    id, organization_id, total_employees, full_time_employees,
    part_time_employees, contract_employees, average_employees, annual_revenue,
    ebitda, total_assets, total_facilities, total_floor_area_sqft,
    occupied_floor_area_sqft, renewable_energy_percentage,
    carbon_offset_percentage, energy_intensity, reporting_standard,
    fiscal_year_start, fiscal_year_end, primary_contact_name,
    primary_contact_email, primary_contact_phone, sustainability_officer_name,
    sustainability_officer_email, industry_sector, naics_code, sic_code,
    custom_metrics, created_at, updated_at, updated_by,
    total_floor_area_sqm, occupied_floor_area_sqm
"""

#: ``organizations`` columns a customer admin may update (all real V3M2
#: columns). Subscription/billing-state and system-managed columns are read-only.
_PROFILE_UPDATE_FIELDS = (
    "name", "company_number", "industry", "sector", "company_size",
    "vat_number", "registration_number", "registered_address", "country",
    "timezone", "currency", "financial_year_end", "reporting_standard",
    "secr_enabled", "esrs_enabled", "issb_enabled", "default_factor_year",
    "preferred_units", "website", "primary_contact_email", "primary_contact_name",
    "billing_contact_email", "billing_contact_name", "billing_address",
    "address_line1", "address_line2", "city", "county", "postcode",
    "eircode", "language", "locale", "business_structure",
    "reporting_frequency", "accounting_standard", "sustainability_standard",
    "data_protection_officer", "privacy_policy_url", "terms_url",
)

#: ``organization_metadata`` columns a customer admin may update (real columns).
_METADATA_UPDATE_FIELDS = (
    "total_employees", "full_time_employees", "part_time_employees",
    "contract_employees", "average_employees", "annual_revenue",
    "total_floor_area_sqm", "occupied_floor_area_sqm",
    "total_floor_area_sqft", "occupied_floor_area_sqft",
    "renewable_energy_percentage", "carbon_offset_percentage",
    "industry_sector", "naics_code", "sic_code",
    "fiscal_year_start", "fiscal_year_end",
    "primary_contact_name", "primary_contact_email", "primary_contact_phone",
    "sustainability_officer_name", "sustainability_officer_email",
    "reporting_standard",
)

_FACILITY_COLUMNS = """
    id, organization_id, name, address_line1, address_line2, city, county,
    postcode, is_active, type, country
"""

_ASSET_COLUMNS = (
    "a.id, a.facility_id, a.organization_id, a.name, a.type AS asset_type, "
    "a.is_active, f.name AS facility_name"
)


def _row_to_org(row: Any) -> Organization:
    r = dict(row)
    return Organization(
        id=str(r["id"]),
        name=str(r["name"]),
        country=str(r.get("country") or "GB"),
        is_active=bool(r["is_active"]),
        created_at=r["created_at"],
        billing_mode=r.get("billing_mode"),
    )


def _row_to_member(row: Any) -> OrganizationMember:
    r = dict(row)
    return OrganizationMember(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        user_id=str(r["user_id"]),
        role=str(r["role"]),
        is_active=bool(r.get("is_active", True)),
        created_at=r.get("created_at"),
    )


def _row_to_metadata(row: Any) -> OrganizationMetadata:
    r = dict(row)
    return OrganizationMetadata(
        total_floor_area_sqm=_as_float(r.get("total_floor_area_sqm")),
        occupied_floor_area_sqm=_as_float(r.get("occupied_floor_area_sqm")),
        fte_count=_as_int(r.get("average_employees")),
        annual_revenue_gbp=_as_float(r.get("annual_revenue")),
        sector=r.get("industry_sector"),
    )


def _iso(value: Any) -> Optional[str]:
    """ISO-8601 for timestamps/dates (or ``None``)."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _row_to_org_full(row: Any) -> dict:
    """Map a full ``organizations`` row to the API-facing profile dict."""
    r = dict(row)
    return {
        "id": str(r["id"]),
        "name": str(r["name"]),
        "country": r.get("country"),
        "is_active": bool(r.get("is_active", True)),
        "created_at": _iso(r.get("created_at")),
        "updated_at": _iso(r.get("updated_at")),
        "billing_mode": r.get("billing_mode"),
        "company_number": r.get("company_number"),
        "logo_url": r.get("logo_url"),
        "industry": r.get("industry"),
        "sector": r.get("sector"),
        "company_size": r.get("company_size"),
        "vat_number": r.get("vat_number"),
        "registration_number": r.get("registration_number"),
        "registered_address": r.get("registered_address"),
        "timezone": r.get("timezone"),
        "currency": r.get("currency"),
        "financial_year_end": _iso(r.get("financial_year_end")),
        "reporting_standard": r.get("reporting_standard"),
        "secr_enabled": bool(r.get("secr_enabled", False)),
        "esrs_enabled": bool(r.get("esrs_enabled", False)),
        "issb_enabled": bool(r.get("issb_enabled", False)),
        "default_factor_year": _as_int(r.get("default_factor_year")),
        "preferred_units": r.get("preferred_units"),
        "website": r.get("website"),
        "primary_contact_email": r.get("primary_contact_email"),
        "primary_contact_name": r.get("primary_contact_name"),
        "billing_contact_email": r.get("billing_contact_email"),
        "billing_contact_name": r.get("billing_contact_name"),
        "subscription_status": r.get("subscription_status"),
        "subscription_tier": r.get("subscription_tier"),
        "billing_address": r.get("billing_address"),
        "tax_rate": _as_float(r.get("tax_rate")),
        "metadata": loads_jsonb(r.get("metadata")) if r.get("metadata") is not None else {},
        "address_line1": r.get("address_line1"),
        "address_line2": r.get("address_line2"),
        "city": r.get("city"),
        "county": r.get("county"),
        "postcode": r.get("postcode"),
        "eircode": r.get("eircode"),
        "language": r.get("language"),
        "locale": r.get("locale"),
        "vat_region": r.get("vat_region"),
        "vat_registered": bool(r.get("vat_registered", False)),
        "tax_region": r.get("tax_region"),
        "registration_region": r.get("registration_region"),
        "sic_code": r.get("sic_code"),
        "naics_code": r.get("naics_code"),
        "nace_code": r.get("nace_code"),
        "business_structure": r.get("business_structure"),
        "is_public": bool(r.get("is_public", False)),
        "is_listed": bool(r.get("is_listed", False)),
        "reporting_frequency": r.get("reporting_frequency"),
        "accounting_standard": r.get("accounting_standard"),
        "sustainability_standard": r.get("sustainability_standard"),
        "carbon_tax_region": r.get("carbon_tax_region"),
        "data_protection_officer": r.get("data_protection_officer"),
        "privacy_policy_url": r.get("privacy_policy_url"),
        "terms_url": r.get("terms_url"),
    }


def _row_to_metadata_full(row: Any) -> dict:
    """Map a full ``organization_metadata`` row to the API-facing dict."""
    r = dict(row)
    return {
        "organization_id": str(r["organization_id"]),
        "total_employees": _as_int(r.get("total_employees")),
        "full_time_employees": _as_int(r.get("full_time_employees")),
        "part_time_employees": _as_int(r.get("part_time_employees")),
        "contract_employees": _as_int(r.get("contract_employees")),
        "average_employees": _as_int(r.get("average_employees")),
        "annual_revenue": _as_float(r.get("annual_revenue")),
        "ebitda": _as_float(r.get("ebitda")),
        "total_assets": _as_float(r.get("total_assets")),
        "total_facilities": _as_int(r.get("total_facilities")),
        "total_floor_area_sqft": _as_float(r.get("total_floor_area_sqft")),
        "occupied_floor_area_sqft": _as_float(r.get("occupied_floor_area_sqft")),
        "renewable_energy_percentage": _as_float(r.get("renewable_energy_percentage")),
        "carbon_offset_percentage": _as_float(r.get("carbon_offset_percentage")),
        "energy_intensity": _as_float(r.get("energy_intensity")),
        "reporting_standard": r.get("reporting_standard"),
        "fiscal_year_start": _iso(r.get("fiscal_year_start")),
        "fiscal_year_end": _iso(r.get("fiscal_year_end")),
        "primary_contact_name": r.get("primary_contact_name"),
        "primary_contact_email": r.get("primary_contact_email"),
        "primary_contact_phone": r.get("primary_contact_phone"),
        "sustainability_officer_name": r.get("sustainability_officer_name"),
        "sustainability_officer_email": r.get("sustainability_officer_email"),
        "industry_sector": r.get("industry_sector"),
        "naics_code": r.get("naics_code"),
        "sic_code": r.get("sic_code"),
        "custom_metrics": (
            loads_jsonb(r.get("custom_metrics")) if r.get("custom_metrics") is not None else {}
        ),
        "total_floor_area_sqm": _as_float(r.get("total_floor_area_sqm")),
        "occupied_floor_area_sqm": _as_float(r.get("occupied_floor_area_sqm")),
        "updated_at": _iso(r.get("updated_at")),
        "updated_by": str(r["updated_by"]) if r.get("updated_by") else None,
    }


def _row_to_member_with_email(row: Any) -> dict:
    """Map a member row joined with the ``users`` email/name columns."""
    r = dict(row)
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "user_id": str(r["user_id"]),
        "role": str(r["role"]),
        "is_active": bool(r.get("is_active", True)),
        "created_at": _iso(r.get("created_at")),
        "email": r.get("user_email"),
        "first_name": r.get("user_first_name"),
        "last_name": r.get("user_last_name"),
    }


def _row_to_facility(row: Any) -> Facility:
    r = dict(row)
    parts = [
        str(r.get(col) or "")
        for col in ("address_line1", "address_line2", "city", "county")
    ]
    return Facility(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        address=", ".join(p for p in parts if p),
        postcode=r.get("postcode"),
        is_active=bool(r.get("is_active", True)),
        type=r.get("type"),
        country=str(r.get("country") or "GB"),
    )


def _row_to_asset(row: Any) -> Asset:
    r = dict(row)
    return Asset(
        id=str(r["id"]),
        facility_id=str(r["facility_id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else "",
        name=str(r["name"]),
        asset_type=str(r.get("asset_type") or "other"),
        facility_name=r.get("facility_name"),
        is_active=bool(r.get("is_active", True)),
    )


def _as_float(value: Any) -> Optional[float]:
    return float(value) if value is not None else None


def _as_int(value: Any) -> Optional[int]:
    return int(value) if value is not None else None

class OrganizationsRepository(AbstractRepository[Organization]):
    """CRUD and lookup for organisations and their child structures."""

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Return the organisation with ``org_id``, or ``None``."""
        return await self.get(org_id)
    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Return the organisation with ``org_id``, or ``None``."""
        return await self.get(org_id)

    async def get_full(self, org_id: str) -> Optional[dict]:
        """Return the full ``organizations`` row (dict) or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ORG_FULL_COLUMNS} FROM public.organizations WHERE id = $1",
            org_id,
        )
        return dict(row) if row is not None else None

    async def set_customer_type(self, org_id: str, customer_type: str) -> bool:
        """Set the informational customer_type label (direct/consultant_managed).

        NEVER authorization — access is always derived from memberships/grants.
        """
        if customer_type not in ("direct", "consultant_managed"):
            raise ValueError(f"unknown customer_type {customer_type!r}")
        row = await self._fetch_one(
            "UPDATE public.organizations SET customer_type = $2, "
            "updated_at = NOW() WHERE id = $1 RETURNING id",
            org_id,
            customer_type,
        )
        return row is not None


    async def get_members(self, org_id: str) -> list[OrganizationMember]:
        """Return every member of the organisation with their roles."""
        rows = await self._fetch_all(
            f"""
            SELECT {_MEMBER_COLUMNS} FROM public.organization_members
            WHERE organization_id = $1
            ORDER BY created_at, id
            """,
            org_id,
        )
        return [_row_to_member(r) for r in rows]

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        """Return the organisation's metadata, or ``None`` when absent."""
        row = await self._fetch_one(
            f"""
            SELECT {_METADATA_COLUMNS} FROM public.organization_metadata
            WHERE organization_id = $1
            LIMIT 1
            """,
            org_id,
        )
        return _row_to_metadata(row) if row is not None else None

    async def get_profile(self, org_id: str) -> Optional[dict]:
        """Return the full organisation profile row (real V3M2 columns)."""
        row = await self._fetch_one(
            f"SELECT {_ORG_FULL_COLUMNS} FROM public.organizations WHERE id = $1",
            org_id,
        )
        return _row_to_org_full(row) if row is not None else None

    async def get_metadata_full(self, org_id: str) -> Optional[dict]:
        """Return the full ``organization_metadata`` row (real columns)."""
        row = await self._fetch_one(
            f"""
            SELECT {_METADATA_FULL_COLUMNS} FROM public.organization_metadata
            WHERE organization_id = $1
            LIMIT 1
            """,
            org_id,
        )
        return _row_to_metadata_full(row) if row is not None else None

    async def update_profile(
        self, org_id: str, fields: dict[str, Any]
    ) -> Optional[dict]:
        """Update the whitelisted real profile columns and return the row.

        Unknown/unwritable fields are rejected by the caller (the API layer);
        only ``_PROFILE_UPDATE_FIELDS`` columns are ever written here. The
        ``organizations`` table carries no ``updated_by`` column, so only the
        ``updated_at`` timestamp is stamped.
        """
        settable = {k: v for k, v in fields.items() if k in _PROFILE_UPDATE_FIELDS}
        if not settable:
            return await self.get_profile(org_id)
        sets, args = ["updated_at = NOW()"], [org_id]
        for column, value in settable.items():
            args.append(value)
            sets.append(f"{column} = ${len(args)}")
        row = await self._fetch_one(
            f"UPDATE public.organizations SET {', '.join(sets)} "
            f"WHERE id = $1 RETURNING {_ORG_FULL_COLUMNS}",
            *args,
        )
        return _row_to_org_full(row) if row is not None else None

    async def update_metadata_full(
        self, org_id: str, fields: dict[str, Any], updated_by: Optional[str] = None
    ) -> Optional[dict]:
        """Upsert the whitelisted real metadata columns and return the row."""
        settable = {k: v for k, v in fields.items() if k in _METADATA_UPDATE_FIELDS}
        if not settable:
            return await self.get_metadata_full(org_id)
        exists = await self.get_metadata_full(org_id)
        if exists is not None:
            sets, args = ["updated_at = NOW()"], []
            for column, value in settable.items():
                args.append(value)
                sets.append(f"{column} = ${len(args)}")
            row = await self._fetch_one(
                f"UPDATE public.organization_metadata SET {', '.join(sets)} "
                f"WHERE organization_id = $1 RETURNING {_METADATA_FULL_COLUMNS}",
                org_id,
                *args,
            )
        else:
            columns = list(settable.keys())
            values = list(settable.values())
            placeholders = [f"${i + 1}" for i in range(len(values))]
            row = await self._fetch_one(
                f"INSERT INTO public.organization_metadata "
                f"(organization_id, {', '.join(columns)}, created_at, updated_at) "
                f"VALUES ($1, {', '.join(placeholders)}, NOW(), NOW()) "
                f"RETURNING {_METADATA_FULL_COLUMNS}",
                org_id,
                *values,
            )
        if row is None:
            return None
        return _row_to_metadata_full(row)

    async def list_members_with_email(self, org_id: str) -> list[dict]:
        """Return members joined with their ``users`` email/name (real data)."""
        rows = await self._fetch_all(
            f"""
            SELECT {_MEMBER_EMAIL_COLUMNS}
            FROM public.organization_members m
            LEFT JOIN public.users u ON u.id = m.user_id
            WHERE m.organization_id = $1
            ORDER BY m.created_at, m.id
            """,
            org_id,
        )
        return [_row_to_member_with_email(r) for r in rows]

    async def get_member(self, member_id: str) -> Optional[dict]:
        """Return a single member joined with their ``users`` row."""
        row = await self._fetch_one(
            f"""
            SELECT {_MEMBER_EMAIL_COLUMNS}
            FROM public.organization_members m
            LEFT JOIN public.users u ON u.id = m.user_id
            WHERE m.id = $1
            """,
            member_id,
        )
        return _row_to_member_with_email(row) if row is not None else None

    async def get_facilities(self, org_id: str) -> list[Facility]:
        """Return every facility belonging to the organisation."""
        rows = await self._fetch_all(
            f"""
            SELECT {_FACILITY_COLUMNS} FROM public.facilities
            WHERE organization_id = $1
            ORDER BY name, id
            """,
            org_id,
        )
        return [_row_to_facility(r) for r in rows]

    async def get_assets(self, org_id: str) -> list[Asset]:
        """Return every asset belonging to the organisation.

        ISC-4 / CL-19 — the list joins ``facilities`` so the human-readable
        facility name is available to the UI (never a bare UUID).
        """
        rows = await self._fetch_all(
            f"""
            SELECT {_ASSET_COLUMNS}
            FROM public.assets a
            LEFT JOIN public.facilities f ON f.id = a.facility_id
            WHERE a.organization_id = $1
            ORDER BY a.name, a.id
            """,
            org_id,
        )
        return [_row_to_asset(r) for r in rows]

    async def get(self, id: str) -> Optional[Organization]:
        """Return the organisation with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_ORG_COLUMNS} FROM public.organizations WHERE id = $1",
            id,
        )
        return _row_to_org(row) if row is not None else None

    async def list_all(self) -> list[Organization]:
        """Return every organisation, by name (operations surface)."""
        rows = await self._fetch_all(
            f"SELECT {_ORG_COLUMNS} FROM public.organizations ORDER BY name, id"
        )
        return [_row_to_org(r) for r in rows]

    async def save(self, entity: Organization) -> Organization:
        """Upsert an organisation by id and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organizations (id, name, country, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                country = EXCLUDED.country,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING {_ORG_COLUMNS}
            """,
            entity.id,
            entity.name,
            entity.country,
            entity.is_active,
        )
        if row is None:
            raise RuntimeError("organization upsert returned no row")
        return _row_to_org(row)

    async def create_with_owner(
        self,
        *,
        org_id: str,
        name: str,
        country: Optional[str],
        owner_user_id: str,
        primary_contact_email: Optional[str] = None,
        company_number: Optional[str] = None,
        billing_mode: Optional[str] = None,
    ) -> dict:
        """Atomically create an organisation and its initial OWNER membership.

        D35 self-service onboarding: a single transaction creates both rows so
        the creator is never left with an organisation they do not own. The
        creator becomes ``owner`` via the real ``organization_members`` role
        model — no second role system is introduced. RLS is not bypassed by a
        browser: this runs server-side through the service-role pool and the
        resulting membership is what authorizes the owner's subsequent
        RLS-scoped requests.

        ``primary_contact_email`` (the creator's verified auth email) is stored
        so the org is discoverable through the D19 email-domain candidate
        signal for future direct customers. ``company_number`` is persisted so
        the D19 exact-company-number duplicate signal works for future
        onboarding lookups. ``billing_mode`` (CREDIT | STANDARD) is the
        per-customer commercial mode resolved from the versioned default at
        creation time (D37-0 §11).

        Returns:
            ``{"organization": Organization, "member": OrganizationMember}``.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                org_row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.organizations
                        (id, name, country, company_number, is_active,
                         primary_contact_email, billing_mode, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, TRUE, $5, $6, NOW(), NOW())
                    RETURNING {_ORG_COLUMNS}
                    """,
                    org_id,
                    name,
                    country,
                    company_number,
                    primary_contact_email,
                    billing_mode,
                )
                if org_row is None:
                    raise RuntimeError("organizations insert returned no row")
                # Ensure the creator exists in ``public.users`` (the
                # organization_members.user_id FK target). Supabase Auth users
                # live in auth.users; the D35 trigger mirrors them, and this
                # server-side upsert is the defensive backstop for users that
                # predate it. Idempotent.
                await conn.execute(
                    """
                    INSERT INTO public.users (id, email, is_active, email_verified, created_at, updated_at)
                    VALUES ($1, $2, TRUE, TRUE, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, updated_at = NOW()
                    """,
                    owner_user_id,
                    primary_contact_email,
                )
                member_row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.organization_members (
                        organization_id, user_id, role, is_active, created_at
                    ) VALUES ($1, $2, 'owner', TRUE, NOW())
                    RETURNING {_MEMBER_COLUMNS}
                    """,
                    org_id,
                    owner_user_id,
                )
                if member_row is None:
                    raise RuntimeError("organization_members insert returned no row")
        return {"organization": _row_to_org(org_row), "member": _row_to_member(member_row)}

    async def get_active_memberships_for_user(self, user_id: str) -> list[OrganizationMember]:
        """Every ACTIVE organisation membership for ``user_id``.

        Used by the self-service org-creation guard: a user who already belongs
        to an active organisation may not silently create a second one through
        the onboarding endpoint (they already have a tenancy context).
        """
        rows = await self._fetch_all(
            f"SELECT {_MEMBER_COLUMNS} FROM public.organization_members "
            "WHERE user_id = $1 AND is_active = TRUE ORDER BY created_at",
            user_id,
        )
        return [_row_to_member(r) for r in rows]

    async def get_billing_mode(self, org_id: str) -> Optional[str]:
        """The per-customer commercial mode (CREDIT | STANDARD), D37-0."""
        row = await self._fetch_one(
            "SELECT billing_mode FROM public.organizations WHERE id = $1",
            org_id,
        )
        return row["billing_mode"] if row is not None else None

    async def delete(self, id: str) -> None:
        """Delete an organisation (cascades to its child rows)."""
        await self._execute(
            "DELETE FROM public.organizations WHERE id = $1", id
        )

    async def update_metadata(
        self, org_id: str, data: OrganizationMetadata
    ) -> OrganizationMetadata:
        """Upsert the organisation's metadata row and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organization_metadata (
                organization_id, total_floor_area_sqm, occupied_floor_area_sqm,
                average_employees, annual_revenue, industry_sector,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
            ON CONFLICT (organization_id)
            DO UPDATE SET
                total_floor_area_sqm = EXCLUDED.total_floor_area_sqm,
                occupied_floor_area_sqm = EXCLUDED.occupied_floor_area_sqm,
                average_employees = EXCLUDED.average_employees,
                annual_revenue = EXCLUDED.annual_revenue,
                industry_sector = EXCLUDED.industry_sector,
                updated_at = NOW()
            RETURNING {_METADATA_COLUMNS}
            """,
            org_id,
            data.total_floor_area_sqm,
            data.occupied_floor_area_sqm,
            data.fte_count,
            data.annual_revenue_gbp,
            data.sector,
        )
        if row is None:
            raise RuntimeError("organization metadata upsert returned no row")
        return _row_to_metadata(row)

