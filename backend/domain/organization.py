"""Organisation structure domain objects (Backend v2.1 §9, ADR-10).

Pure Python, immutable frozen dataclasses. Mirror the RC2
``organizations`` / ``facilities`` / ``assets`` tables.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Organization:
    """A customer organisation (the top-level tenant)."""

    id: str
    name: str
    country: str
    is_active: bool
    created_at: datetime
    billing_mode: Optional[str] = None


@dataclass(frozen=True, slots=True)
class OrganizationMember:
    """A member of an organisation with a platform role (admin/editor/viewer).

    Mirrors the RC2 ``organization_members`` table.
    """

    id: str
    organization_id: str
    user_id: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Facility:
    """A physical site belonging to an organisation."""

    id: str
    organization_id: str
    name: str
    address: str
    postcode: Optional[str] = None
    # ISC-7 / MD-1 — surfaced so the locations/facilities UI can show real
    # lifecycle state and classification (previously omitted → every facility
    # rendered as "Inactive").
    is_active: bool = True
    type: Optional[str] = None
    country: Optional[str] = "GB"


@dataclass(frozen=True, slots=True)
class Asset:
    """An individual asset located at a facility (meter, vehicle, boiler, ...)."""

    id: str
    facility_id: str
    organization_id: str
    name: str
    asset_type: str
    # ISC-4 / CL-19 — the asset list renders the human-readable facility name
    # instead of the raw UUID; is_active mirrors the schema.
    facility_name: Optional[str] = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class OrganizationMetadata:
    """Key figures used by area-based and spend-based methodologies.

    Values are optional because they are populated gradually as the
    organisation provides profile data.
    """

    total_floor_area_sqm: Optional[float] = None
    occupied_floor_area_sqm: Optional[float] = None
    fte_count: Optional[int] = None
    annual_revenue_gbp: Optional[float] = None
    sector: Optional[str] = None
