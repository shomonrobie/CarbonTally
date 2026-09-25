"""P17-IMPLEMENT-10 — product-contract dimensions (domain layer).

Covers the two persisted facts this task added, at the level where the rules
live, plus the security property that makes them safe:

* ``transaction_provider`` (P17-PRODUCT-01 §5) — where the activity was
  PURCHASED, deliberately distinct from the supplier whose activity generated the
  emissions. It is a bounded NAME, never a supplier reference, which is precisely
  why it cannot be used to forge a cross-tenant reference: there is no id to
  forge.
* ``scope3_method`` (P17-PRODUCT-01 §29/§34) — the category-specific accounting
  methodology, validated fail-closed against the frozen contract vocabulary.

Pure: no database, no provider, no I/O.
"""
from __future__ import annotations

import pytest

from core.exceptions import (
    AccountingDimensionError,
    Scope3MethodNotSupportedError,
)
from domain.accounting_dimensions import (
    TRANSACTION_PROVIDER_MAX_LENGTH,
    AccountingDimensions,
)
from domain.scope3_contracts import (
    SCOPE3_METHODS,
    methods_for,
    validate_scope3_method_for_category,
)


# ---------------------------------------------------------------------------
# transaction_provider vs underlying supplier (P17-PRODUCT-01 §5)
# ---------------------------------------------------------------------------
def test_provider_and_supplier_are_separate_facts() -> None:
    """Both facts are carried at once and neither is derived from the other."""
    dimensions = AccountingDimensions(
        scope3_category=6,
        scope3_method="distance_based",
        transaction_provider="Booking.com",
    )
    names = set(dimensions.as_columns())
    assert "transaction_provider" in names
    assert "scope3_method" in names
    # Supplier attribution is NOT an accounting dimension: it is carried on the
    # calculation request / emissions log instead.
    assert "supplier_id" not in names


def test_a_blank_provider_is_refused_rather_than_stored_as_known() -> None:
    for blank in ("", "   ", "\t"):
        with pytest.raises(AccountingDimensionError):
            AccountingDimensions(
                scope3_category=1, transaction_provider=blank
            ).validate_for_scope("Scope 3")


def test_an_over_long_provider_is_refused() -> None:
    too_long = "x" * (TRANSACTION_PROVIDER_MAX_LENGTH + 1)
    with pytest.raises(AccountingDimensionError):
        AccountingDimensions(
            scope3_category=1, transaction_provider=too_long
        ).validate_for_scope("Scope 3")


def test_control_characters_in_a_provider_are_refused() -> None:
    for bad in ("Booking\n.com", "Booking\tcom", "Booking\x7f.com"):
        with pytest.raises(AccountingDimensionError):
            AccountingDimensions(
                scope3_category=1, transaction_provider=bad
            ).validate_for_scope("Scope 3")


def test_absent_provider_is_valid_and_writes_null() -> None:
    """Unknown stays unknown: the provider is never back-filled from anything."""
    dimensions = AccountingDimensions(scope3_category=6)
    dimensions.validate_for_scope("Scope 3")
    assert dimensions.as_columns()["transaction_provider"] is None



# ---------------------------------------------------------------------------
# scope3_method (P17-PRODUCT-01 §29/§34)
# ---------------------------------------------------------------------------
def test_scope3_method_vocabulary_is_the_contract_union() -> None:
    assert set(SCOPE3_METHODS) == {
        "asset_specific",
        "average_data",
        "distance_based",
        "extrapolated",
        "industry_average",
        "modelled",
        "proxy_data",
        "spend_based",
        "supplier_specific",
        "survey_based",
    }


def test_every_contract_method_is_accepted_by_the_dimension() -> None:
    for method in SCOPE3_METHODS:
        dimensions = AccountingDimensions(scope3_category=6, scope3_method=method)
        dimensions.validate_for_scope("Scope 3")
        assert dimensions.as_columns()["scope3_method"] == method


def test_a_method_outside_the_union_is_refused() -> None:
    with pytest.raises(Scope3MethodNotSupportedError):
        AccountingDimensions(
            scope3_category=6, scope3_method="invented_method"
        ).validate_for_scope("Scope 3")


@pytest.mark.parametrize("category", range(1, 16))
def test_membership_is_validated_against_the_category_own_contract(
    category: int,
) -> None:
    """A method is only accepted where the CATEGORY permits it."""
    for method in methods_for(category):
        assert validate_scope3_method_for_category(category, method) == method
    with pytest.raises(Scope3MethodNotSupportedError):
        validate_scope3_method_for_category(category, "invented_method")


def test_an_absent_method_is_never_defaulted_to_the_first_contract_entry() -> None:
    assert validate_scope3_method_for_category(6, None) is None
    dimensions = AccountingDimensions(scope3_category=6)
    dimensions.validate_for_scope("Scope 3")
    assert dimensions.as_columns()["scope3_method"] is None


def test_scope3_method_on_a_scope2_result_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        AccountingDimensions(
            scope2_method="LOCATION_BASED", scope3_method="average_data"
        ).validate_for_scope("Scope 2")


def test_scope3_method_on_a_scope1_result_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        AccountingDimensions(scope3_method="average_data").validate_for_scope("Scope 1")


# ---------------------------------------------------------------------------
# The new data-quality classifications are usable e2e
# ---------------------------------------------------------------------------
def test_the_product_classifications_are_accepted_dimensions() -> None:
    for quality in ("activity_based", "estimated", "manual", "unresolved"):
        dimensions = AccountingDimensions(scope3_category=1, data_quality=quality)
        dimensions.validate_for_scope("Scope 3")
        assert dimensions.as_columns()["data_quality"] == quality
