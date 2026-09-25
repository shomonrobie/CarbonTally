"""P17 Scope 3 category-framework tests (implementation tests).

Pure, no DB. Locks the architecture's honest status rollup into the code so it
cannot silently drift:

    SUPPORTED [3,4,5,6]   PARTIAL [1,7,8,9,12,13]
    DEFERRED [11,14,15]   NOT_IMPLEMENTED [2,10]

and asserts that a category with no methodology is REFUSED rather than invented,
and that the DC-02/DC-04/DC-05/DC-07 boundaries fail closed.
"""
from __future__ import annotations

import pytest

from core.exceptions import (
    BoundaryAmbiguityError,
    Scope3CategoryNotSupportedError,
    Scope3CategoryRequiredError,
)
from domain.scope3 import (
    CATEGORY_STATUS,
    DEFERRED_CATEGORIES,
    NOT_IMPLEMENTED_CATEGORIES,
    PARTIAL_CATEGORIES,
    SCOPE3_CATEGORIES,
    SUPPORTED_CATEGORIES,
    Scope3Status,
    assert_boundary_complete,
    assert_calculable,
    derives_from_source_snapshot,
    is_calculable,
    requires_estimation_record,
    status_of,
    validate_scope3_category,
)


# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------
def test_taxonomy_has_exactly_fifteen_categories_numbered_1_to_15() -> None:
    numbers = [c.category for c in SCOPE3_CATEGORIES]
    assert len(SCOPE3_CATEGORIES) == 15
    assert numbers == list(range(1, 16))


def test_every_slug_is_unique() -> None:
    slugs = [c.slug for c in SCOPE3_CATEGORIES]
    assert len(set(slugs)) == len(slugs)


def test_downstream_classification_matches_ghg_protocol() -> None:
    """Categories 9-15 are downstream; 1-8 are not."""
    for category in SCOPE3_CATEGORIES:
        expected = category.category >= 9
        assert category.is_downstream is expected, category.slug


def test_category_names_are_the_ghg_protocol_names() -> None:
    names = {c.category: c.name for c in SCOPE3_CATEGORIES}
    assert names[1] == "Purchased goods and services"
    assert names[3] == "Fuel- and energy-related activities"
    assert names[5] == "Waste generated in operations"
    assert names[6] == "Business travel"
    assert names[7] == "Employee commuting"
    assert names[12] == "End-of-life treatment of sold products"
    assert names[15] == "Investments"


# ---------------------------------------------------------------------------
# Status rollup — the architecture's authoritative statuses
# ---------------------------------------------------------------------------
def test_status_rollup_matches_the_architecture_exactly() -> None:
    assert SUPPORTED_CATEGORIES == (3, 4, 5, 6)
    assert PARTIAL_CATEGORIES == (1, 7, 8, 9, 12, 13)
    assert DEFERRED_CATEGORIES == (11, 14, 15)
    assert NOT_IMPLEMENTED_CATEGORIES == (2, 10)


def test_no_category_status_is_unset() -> None:
    assert set(CATEGORY_STATUS) == set(range(1, 16))
    assert len(CATEGORY_STATUS) == 15


def test_categories_2_and_10_are_not_implemented_and_were_not_promoted() -> None:
    """ARCH-05/ARCH-06: no category status may be silently promoted."""
    assert status_of(2) is Scope3Status.NOT_IMPLEMENTED
    assert status_of(10) is Scope3Status.NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Calculability guard
# ---------------------------------------------------------------------------
def test_supported_and_partial_categories_are_calculable() -> None:
    for category in (*SUPPORTED_CATEGORIES, *PARTIAL_CATEGORIES):
        assert is_calculable(category) is True, category


def test_not_implemented_and_deferred_categories_are_not_calculable() -> None:
    for category in (*NOT_IMPLEMENTED_CATEGORIES, *DEFERRED_CATEGORIES):
        assert is_calculable(category) is False, category


@pytest.mark.parametrize("category", [2, 10, 11, 14, 15])
def test_assert_calculable_refuses_unimplemented_and_deferred(category: int) -> None:
    with pytest.raises(Scope3CategoryNotSupportedError) as exc:
        assert_calculable(category)
    details = exc.value.details
    assert details["category"] == category
    assert details["status"] in ("NOT_IMPLEMENTED", "DEFERRED")


def test_assert_calculable_returns_the_definition_for_calculable_categories() -> None:
    definition = assert_calculable(4)
    assert definition.category == 4
    assert definition.status is Scope3Status.SUPPORTED


def test_every_uncalculable_category_documents_its_bounded_path_or_gap() -> None:
    """An unimplemented category must state what is missing, never be silent."""
    by_number = {c.category: c for c in SCOPE3_CATEGORIES}
    for category in (*NOT_IMPLEMENTED_CATEGORIES, *DEFERRED_CATEGORIES):
        assert by_number[category].bounded_path, category


def test_every_category_carries_a_boundary_note() -> None:
    """Overlap with another category must be explained, not merely numbered."""
    for category in SCOPE3_CATEGORIES:
        assert category.boundary_note.strip(), category.slug


# ---------------------------------------------------------------------------
# Vocabulary validation
# ---------------------------------------------------------------------------
def test_none_category_is_permitted() -> None:
    assert validate_scope3_category(None) is None


@pytest.mark.parametrize("value", [0, 16, -1, 100])
def test_out_of_range_categories_are_refused(value: int) -> None:
    with pytest.raises(Scope3CategoryRequiredError):
        validate_scope3_category(value)


@pytest.mark.parametrize("value", [True, False])
def test_boolean_is_not_a_category(value: bool) -> None:
    with pytest.raises(Scope3CategoryRequiredError):
        validate_scope3_category(value)


@pytest.mark.parametrize("value", [1, 8, 15])
def test_in_range_categories_validate(value: int) -> None:
    assert validate_scope3_category(value) == value


# ---------------------------------------------------------------------------
# DC-02 / DC-04 / DC-05 / DC-07 boundary controls
# ---------------------------------------------------------------------------
def test_dc04_requires_a_transport_boundary_for_categories_4_and_9() -> None:
    for category in (4, 9):
        with pytest.raises(BoundaryAmbiguityError) as exc:
            assert_boundary_complete(category=category)
        assert exc.value.details["control"] == "DC-04"
        assert exc.value.details["field"] == "transport_boundary"


def test_dc04_is_satisfied_by_a_matching_boundary() -> None:
    assert_boundary_complete(category=4, transport_boundary="upstream")
    assert_boundary_complete(category=9, transport_boundary="downstream")


def test_dc04_refuses_a_boundary_that_contradicts_the_category() -> None:
    """An 'upstream' boundary on category 9 is a contradiction, not a nuance."""
    with pytest.raises(BoundaryAmbiguityError) as exc:
        assert_boundary_complete(category=9, transport_boundary="upstream")
    assert exc.value.details["control"] == "DC-04"
    with pytest.raises(BoundaryAmbiguityError):
        assert_boundary_complete(category=4, transport_boundary="downstream")


def test_dc05_requires_a_waste_origin_for_categories_5_and_12() -> None:
    for category in (5, 12):
        with pytest.raises(BoundaryAmbiguityError) as exc:
            assert_boundary_complete(category=category)
        assert exc.value.details["control"] == "DC-05"


def test_dc05_is_satisfied_by_a_matching_origin() -> None:
    assert_boundary_complete(category=5, waste_origin="operations")
    assert_boundary_complete(category=12, waste_origin="sold_product_eol")


def test_dc05_refuses_an_origin_that_contradicts_the_category() -> None:
    with pytest.raises(BoundaryAmbiguityError):
        assert_boundary_complete(category=5, waste_origin="sold_product_eol")


def test_dc07_fails_closed_when_the_consolidation_approach_is_undecided() -> None:
    for category in (8, 13):
        with pytest.raises(BoundaryAmbiguityError) as exc:
            assert_boundary_complete(category=category, consolidation_approach=None)
        assert exc.value.details["control"] == "DC-07"


def test_dc07_is_satisfied_once_the_approach_is_decided() -> None:
    assert_boundary_complete(category=8, consolidation_approach="OPERATIONAL_CONTROL")
    assert_boundary_complete(category=13, consolidation_approach="EQUITY_SHARE")


def test_dc02_requires_category_3_to_link_its_source_snapshot() -> None:
    with pytest.raises(BoundaryAmbiguityError) as exc:
        assert_boundary_complete(category=3)
    assert exc.value.details["control"] == "DC-02"
    assert exc.value.details["field"] == "source_snapshot_id"


def test_dc02_is_satisfied_by_a_source_snapshot_link() -> None:
    assert_boundary_complete(category=3, source_snapshot_id="snap-1")


def test_only_category_3_derives_from_a_source_snapshot() -> None:
    assert derives_from_source_snapshot(3) is True
    for category in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
        assert derives_from_source_snapshot(category) is False


def test_no_boundary_rule_applies_when_no_category_is_recorded() -> None:
    """Historical P16 rows carry no category and must remain valid."""
    assert_boundary_complete(category=None) is None


def test_estimation_categories_are_the_estimated_paths() -> None:
    assert requires_estimation_record(7) is True
    assert requires_estimation_record(11) is True
    assert requires_estimation_record(12) is True
    assert requires_estimation_record(14) is True
    assert requires_estimation_record(6) is False
    assert requires_estimation_record(None) is False