"""Unit tests for domain.organization."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.organization import Asset, Facility, Organization, OrganizationMetadata


def utc_now() -> datetime:
    return datetime(2025, 1, 1, tzinfo=timezone.utc)


class TestOrganization:
    def test_constructs(self) -> None:
        org = Organization(
            id="org-1",
            name="Acme Ltd",
            country="GB",
            is_active=True,
            created_at=utc_now(),
        )
        assert org.country == "GB"

    def test_is_immutable(self) -> None:
        org = Organization(
            id="org-1", name="Acme Ltd", country="GB", is_active=True, created_at=utc_now()
        )
        with pytest.raises(FrozenInstanceError):
            org.name = "Renamed"  # type: ignore[misc]


class TestFacility:
    def test_constructs(self) -> None:
        facility = Facility(
            id="fac-1",
            organization_id="org-1",
            name="London HQ",
            address="1 Main St",
            postcode="SW1A 1AA",
        )
        assert facility.postcode == "SW1A 1AA"


class TestAsset:
    def test_constructs(self) -> None:
        asset = Asset(
            id="a-1",
            facility_id="fac-1",
            organization_id="org-1",
            name="Boiler 1",
            asset_type="boiler",
        )
        assert asset.asset_type == "boiler"


class TestOrganizationMetadata:
    def test_defaults_are_none(self) -> None:
        metadata = OrganizationMetadata()
        assert metadata.total_floor_area_sqm is None
        assert metadata.sector is None

    def test_constructs(self) -> None:
        metadata = OrganizationMetadata(
            total_floor_area_sqm=1200.5,
            fte_count=45,
            annual_revenue_gbp=5_000_000,
            sector="Retail",
        )
        assert metadata.sector == "Retail"
