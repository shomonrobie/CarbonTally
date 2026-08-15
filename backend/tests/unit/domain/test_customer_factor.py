"""Unit tests for the Customer Factor domain (V3 ADR-V3-002)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from domain.customer_factor import (
    CUSTOMER_FACTOR_COUNTRIES,
    CUSTOMER_FACTOR_SOURCE,
    CUSTOMER_FACTOR_STATUSES,
    CustomerFactor,
)


def make_factor(**overrides) -> CustomerFactor:
    defaults = dict(
        id="cf-1",
        organization_id="org-a",
        name="My Electricity Factor",
        activity_type="Electricity",
        co2e_multiplier=Decimal("0.20"),
        reporting_year=2025,
    )
    defaults.update(overrides)
    return CustomerFactor(**defaults)


class TestCustomerFactor:
    def test_valid_factor(self) -> None:
        factor = make_factor()
        assert factor.status == "draft"
        assert factor.version == 1
        assert factor.factor_source == "CUSTOMER"

    def test_rejects_negative_multiplier(self) -> None:
        with pytest.raises(ValueError):
            make_factor(co2e_multiplier=Decimal("-0.1"))

    def test_rejects_bad_country(self) -> None:
        with pytest.raises(ValueError):
            make_factor(country="FR")

    def test_rejects_bad_status(self) -> None:
        with pytest.raises(ValueError):
            make_factor(status="bogus")

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError):
            make_factor(reporting_year=1800)

    def test_immutable(self) -> None:
        factor = make_factor()
        with pytest.raises(AttributeError):
            factor.name = "Changed"  # type: ignore[misc]

    def test_transition_lifecycle(self) -> None:
        assert make_factor().can_transition_to("active")
        assert make_factor().can_transition_to("inactive")
        active = make_factor(status="active")
        assert active.can_transition_to("inactive")
        assert active.can_transition_to("archived")
        archived = make_factor(status="archived")
        assert not archived.can_transition_to("active")

    def test_vocabularies(self) -> None:
        assert set(CUSTOMER_FACTOR_STATUSES) == {
            "draft", "active", "inactive", "archived"
        }
        assert CUSTOMER_FACTOR_SOURCE == "CUSTOMER"
        assert set(CUSTOMER_FACTOR_COUNTRIES) == {"GB", "IE"}
