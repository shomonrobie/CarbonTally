"""P17 Scope 3 category framework (ARCH-01 Scope 3, P17-D/P17-E/F/G).

Pure Python. No framework, database or infrastructure imports.

Fifteen GHG Protocol categories, and — critically — an HONEST statement of which
of them has a supported methodology today. The architecture's authoritative
status rollup is:

    SUPPORTED       [3, 4, 5, 6]
    PARTIAL         [1, 7, 8, 9, 12, 13]
    DEFERRED        [11, 14, 15]
    NOT_IMPLEMENTED [2, 10]

That status is reproduced here so the implementation cannot silently pretend a
methodology exists. ``NOT_IMPLEMENTED`` and ``DEFERRED`` categories have a
taxonomy, a boundary definition and a lifecycle slot — and **no** calculation
path. Asking for one raises rather than inventing a number.

The distinction this framework exists to make:

* the category TAXONOMY says which categories exist;
* the category STATUS says which may be calculated;
* the category BOUNDARY says how overlapping categories are told apart.

Conflating those three is how double counting and fabricated methodology enter an
inventory.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from core.exceptions import (
    BoundaryAmbiguityError,
    Scope3CategoryNotSupportedError,
    Scope3CategoryRequiredError,
)

__all__ = [
    "Scope3Status",
    "TransportBoundary",
    "WasteOrigin",
    "Scope3Category",
    "SCOPE3_CATEGORIES",
    "CATEGORY_STATUS",
    "SUPPORTED_CATEGORIES",
    "PARTIAL_CATEGORIES",
    "DEFERRED_CATEGORIES",
    "NOT_IMPLEMENTED_CATEGORIES",
    "validate_scope3_category",
    "status_of",
    "definition_of",
    "is_calculable",
    "assert_calculable",
    "categories_requiring_transport_boundary",
    "categories_requiring_waste_origin",
    "categories_requiring_consolidation",
    "assert_boundary_complete",
    "requires_estimation_record",
    "derives_from_source_snapshot",
]


class Scope3Status(StrEnum):
    """The authoritative architecture status of a Scope 3 category."""

    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    DEFERRED = "DEFERRED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class TransportBoundary(StrEnum):
    """DC-04 discriminator: category 4 (upstream) vs category 9 (downstream)."""

    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"


class WasteOrigin(StrEnum):
    """DC-05 discriminator: category 5 (operations) vs category 12 (sold-product EoL)."""

    OPERATIONS = "operations"
    SOLD_PRODUCT_EOL = "sold_product_eol"


@dataclass(frozen=True, slots=True)
class Scope3Category:
    """One GHG Protocol Scope 3 category and its accounting contract.

    Attributes:
        category: The 1-15 identity used by ``calculation_snapshots.scope3_category``.
        slug: Stable machine-readable name (matches ``scope3_categories.slug``).
        name: Human-readable GHG Protocol name.
        is_downstream: GHG Protocol downstream classification.
        status: The authoritative architecture status (not a judgement made here).
        boundary_note: Why this category can be confused with another one.
        bounded_path: For PARTIAL/DEFERRED categories, the exact scope of what is
            or is not implemented. ``None`` means no bounded path is defined.
    """

    category: int
    slug: str
    name: str
    is_downstream: bool
    status: Scope3Status
    boundary_note: str
    bounded_path: Optional[str] = None


#: The 15 categories. Status values are copied verbatim from
#: ``p17_scope3_category_matrix_20250925.json -> status_rollup``.
SCOPE3_CATEGORIES: tuple[Scope3Category, ...] = (
    Scope3Category(
        1, "purchased_goods_and_services", "Purchased goods and services", False,
        Scope3Status.PARTIAL,
        "Shares the supplier-specific / average-data factor family with category 2; "
        "the discriminator is whether the item is consumed in-year (1) or capitalised (2).",
        bounded_path="supplier-specific or average-data factor path on an extracted "
                    "activity line. Spend-based is permitted only where explicitly "
                    "selected and is then marked data_quality='spend_based_estimated'.",
    ),
    Scope3Category(
        2, "capital_goods", "Capital goods", False,
        Scope3Status.NOT_IMPLEMENTED,
        "Confused with category 1 because the factor family is identical; the "
        "discriminator is capitalisation, which the product model does not yet carry.",
        bounded_path="NOT IMPLEMENTED. No methodology is invented. The category has a "
                    "taxonomy row, a boundary note and a lifecycle slot so that the "
                    "gap is explicit and auditable.",
    ),
    Scope3Category(
        3, "fuel_and_energy_related_activities", "Fuel- and energy-related activities", False,
        Scope3Status.SUPPORTED,
        "Must not re-add a quantity already in Scope 1/2; DC-02 requires a persisted "
        "source snapshot link.",
    ),
    Scope3Category(
        4, "upstream_transportation_and_distribution",
        "Upstream transportation and distribution", False,
        Scope3Status.SUPPORTED,
        "Shares the freight factor family with category 9; DC-04 requires an explicit "
        "transport boundary.",
    ),
    Scope3Category(
        5, "waste_generated_in_operations", "Waste generated in operations", False,
        Scope3Status.SUPPORTED,
        "Shares the waste-treatment factor family with category 12; DC-05 requires an "
        "explicit waste origin.",
    ),
    Scope3Category(
        6, "business_travel", "Business travel", False,
        Scope3Status.SUPPORTED,
        "Shares travel factors with category 7; the discriminator is trip purpose, "
        "recorded on the activity rather than inferred from the factor.",
    ),
    Scope3Category(
        7, "employee_commuting", "Employee commuting", False,
        Scope3Status.PARTIAL,
        "Uses estimated average data; T-INV-12 requires a persisted estimation record.",
        bounded_path="average-data commuting estimate with a persisted estimation "
                    "record, marked secondary/estimated. Home-working and "
                    "survey-extrapolated variants are NOT implemented.",
    ),
    Scope3Category(
        8, "upstream_leased_assets", "Upstream leased assets", False,
        Scope3Status.PARTIAL,
        "Depends on the organization consolidation approach (DC-07) and must not "
        "double count an asset already in Scope 1/2.",
        bounded_path="leased asset recorded with an explicit consolidation approach; "
                    "fails closed when the organization has not decided one.",
    ),
    Scope3Category(
        9, "downstream_transportation_and_distribution",
        "Downstream transportation and distribution", True,
        Scope3Status.PARTIAL,
        "Shares the freight factor family with category 4; DC-04 requires an explicit "
        "transport boundary.",
        bounded_path="outbound shipment persisted with an explicit downstream boundary; "
                    "must be provably absent from category 4 totals.",
    ),
    Scope3Category(
        10, "processing_of_sold_products", "Processing of sold products", True,
        Scope3Status.NOT_IMPLEMENTED,
        "Confused with categories 11/12 because all three concern sold products; the "
        "discriminator is the processing stage, which needs the sold-product model.",
        bounded_path="NOT IMPLEMENTED. No methodology is invented; the category carries "
                    "a taxonomy row, a boundary note and a lifecycle slot so the gap is "
                    "explicit.",
    ),
    Scope3Category(
        11, "use_of_sold_products", "Use of sold products", True,
        Scope3Status.DEFERRED,
        "Overlaps categories 12 and 13; the boundary needs the PO product decision.",
        bounded_path="an explicitly persisted lifetime/use assumption set may be "
                    "recorded. DEFERRED because the methodology awaits the PO decision.",
    ),
    Scope3Category(
        12, "end_of_life_treatment_of_sold_products",
        "End-of-life treatment of sold products", True,
        Scope3Status.PARTIAL,
        "Shares the waste-treatment factor family with category 5; DC-05 requires an "
        "explicit waste origin, and the treatment route fails closed where unevidenced.",
        bounded_path="material composition plus an explicit treatment-route assumption, "
                    "persisted as sold_product_eol. Fails closed where the route is not "
                    "evidenced (the P16 waste principle reused verbatim).",
    ),
    Scope3Category(
        13, "downstream_leased_assets", "Downstream leased assets", True,
        Scope3Status.PARTIAL,
        "Mirror of category 8; depends on the consolidation approach (DC-07) and must "
        "not double count the same asset period.",
        bounded_path="leased-out asset with an explicit lessor/consolidation record and "
                    "a negative check against category 8 and Scope 1/2.",
    ),
    Scope3Category(
        14, "franchises", "Franchises", True,
        Scope3Status.DEFERRED,
        "Overlaps Scope 1/2 for franchise-owned sites; the boundary needs the franchise "
        "operating-model decision.",
        bounded_path="an explicitly recorded allocation basis may be stored. DEFERRED "
                    "because the operating model awaits the PO decision.",
    ),
    Scope3Category(
        15, "investments", "Investments", True,
        Scope3Status.DEFERRED,
        "Depends on the consolidation approach and the equity-share boundary.",
        bounded_path="equity share attribution only (attribution_equity_share). "
                    "DEFERRED: the bounded-methodology decision is outstanding.",
    ),
)

#: category number -> category definition
_BY_NUMBER: dict[int, Scope3Category] = {c.category: c for c in SCOPE3_CATEGORIES}

#: category number -> authoritative status
CATEGORY_STATUS: dict[int, Scope3Status] = {
    c.category: c.status for c in SCOPE3_CATEGORIES
}

SUPPORTED_CATEGORIES: tuple[int, ...] = tuple(
    c.category for c in SCOPE3_CATEGORIES if c.status is Scope3Status.SUPPORTED
)
PARTIAL_CATEGORIES: tuple[int, ...] = tuple(
    c.category for c in SCOPE3_CATEGORIES if c.status is Scope3Status.PARTIAL
)
DEFERRED_CATEGORIES: tuple[int, ...] = tuple(
    c.category for c in SCOPE3_CATEGORIES if c.status is Scope3Status.DEFERRED
)
NOT_IMPLEMENTED_CATEGORIES: tuple[int, ...] = tuple(
    c.category for c in SCOPE3_CATEGORIES if c.status is Scope3Status.NOT_IMPLEMENTED
)

#: Categories whose result is meaningless without a DC-04 transport boundary.
_TRANSPORT_BOUNDARY_CATEGORIES: frozenset[int] = frozenset({4, 9})

#: Categories whose result is meaningless without a DC-05 waste origin.
_WASTE_ORIGIN_CATEGORIES: frozenset[int] = frozenset({5, 12})

#: Categories that depend on the organization consolidation approach (DC-07).
_CONSOLIDATION_CATEGORIES: frozenset[int] = frozenset({8, 13})

#: Categories whose adopted bounded path uses estimated data (T-INV-12).
_ESTIMATION_CATEGORIES: frozenset[int] = frozenset({7, 11, 12, 14})


def validate_scope3_category(value: Optional[int]) -> Optional[int]:
    """Return ``value`` when it is a category 1-15, else raise.

    ``None`` is permitted and means "not recorded" — the state every historical
    P16 Scope 3 row legitimately holds.
    """
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 15:
        raise Scope3CategoryRequiredError(
            f"invalid Scope 3 category {value!r}; expected an integer 1-15",
            details={"field": "scope3_category", "received": value},
        )
    return value


def definition_of(category: int) -> Scope3Category:
    """Return the category definition, raising when the category is unknown."""
    validate_scope3_category(category)
    return _BY_NUMBER[int(category)]  # type: ignore[index]


def status_of(category: int) -> Scope3Status:
    """Return the authoritative architecture status of a category."""
    return definition_of(category).status


def is_calculable(category: int) -> bool:
    """True when the architecture provides a calculation path for this category.

    ``SUPPORTED`` and ``PARTIAL`` are calculable (``PARTIAL`` only along its
    bounded path). ``NOT_IMPLEMENTED`` and ``DEFERRED`` are not — and no
    methodology is invented to make them calculable.
    """
    return status_of(category) in (Scope3Status.SUPPORTED, Scope3Status.PARTIAL)


def assert_calculable(category: int) -> Scope3Category:
    """Raise unless the category has an architecture-sanctioned calculation path.

    This is the single guard that keeps a category-taxonomy row from being
    mistaken for an implemented methodology.
    """
    definition = definition_of(category)
    if definition.status in (Scope3Status.NOT_IMPLEMENTED, Scope3Status.DEFERRED):
        raise Scope3CategoryNotSupportedError(
            f"Scope 3 category {definition.category} ({definition.name}) is "
            f"{definition.status.value} in the authoritative architecture; no "
            "methodology is implemented for it and none may be invented",
            details={
                "category": definition.category,
                "status": definition.status.value,
                "bounded_path": definition.bounded_path,
            },
        )
    return definition


def categories_requiring_transport_boundary() -> frozenset[int]:
    """Categories 4 and 9 (DC-04)."""
    return _TRANSPORT_BOUNDARY_CATEGORIES


def categories_requiring_waste_origin() -> frozenset[int]:
    """Categories 5 and 12 (DC-05)."""
    return _WASTE_ORIGIN_CATEGORIES


def categories_requiring_consolidation() -> frozenset[int]:
    """Categories 8 and 13 (DC-07)."""
    return _CONSOLIDATION_CATEGORIES


def requires_estimation_record(category: Optional[int]) -> bool:
    """True when this category's adopted path uses estimated data (T-INV-12)."""
    if category is None:
        return False
    return int(category) in _ESTIMATION_CATEGORIES


def derives_from_source_snapshot(category: Optional[int]) -> bool:
    """True when the category must link to a source Scope 1/2 snapshot (DC-02).

    Only category 3 (fuel- and energy-related activities) is defined this way: it
    is a derivation from an existing Scope 1/2 figure, and the uniqueness index
    ``uq_calc_snapshots_cat3_source`` makes a second derivation for the same
    source snapshot impossible.
    """
    return category == 3


def assert_boundary_complete(
    *,
    category: Optional[int],
    transport_boundary: Optional[str] = None,
    waste_origin: Optional[str] = None,
    consolidation_approach: Optional[str] = None,
    source_snapshot_id: Optional[str] = None,
) -> None:
    """Fail closed when a new Scope 3 result has an ambiguous or missing boundary.

    Implements DC-02, DC-04, DC-05 and DC-07 as one guard, because they are the
    same class of defect: a result whose category cannot be defended. Each check
    raises :class:`BoundaryAmbiguityError` naming the concrete control and field
    so the UI can tell the operator exactly what to supply.

    Classification is by accounting **boundary/origin**, never by factor family: a
    freight factor appearing on a line does not by itself decide whether the line
    is category 4 or 9.
    """
    if category is None:
        return
    category = int(category)

    if category in _TRANSPORT_BOUNDARY_CATEGORIES and transport_boundary is None:
        raise BoundaryAmbiguityError(
            f"DC-04: Scope 3 category {category} requires an explicit transport "
            "boundary (upstream/downstream); without it the result cannot be told "
            "apart from the overlapping transport category",
            details={"control": "DC-04", "category": category,
                     "field": "transport_boundary"},
        )
    if category in _WASTE_ORIGIN_CATEGORIES and waste_origin is None:
        raise BoundaryAmbiguityError(
            f"DC-05: Scope 3 category {category} requires an explicit waste origin "
            "(operations/sold_product_eol); without it the result cannot be told "
            "apart from the overlapping waste category",
            details={"control": "DC-05", "category": category,
                     "field": "waste_origin"},
        )
    if category in _CONSOLIDATION_CATEGORIES and consolidation_approach is None:
        raise BoundaryAmbiguityError(
            f"DC-07: Scope 3 category {category} depends on the organization "
            "consolidation approach, which is undecided; the result fails closed "
            "rather than being counted under an assumption",
            details={"control": "DC-07", "category": category,
                     "field": "consolidation_approach"},
        )
    if derives_from_source_snapshot(category) and source_snapshot_id is None:
        raise BoundaryAmbiguityError(
            "DC-02: Scope 3 category 3 (fuel- and energy-related activities) must "
            "link to the Scope 1/2 snapshot it derives from, so the same quantity "
            "cannot be added twice",
            details={"control": "DC-02", "category": 3,
                     "field": "source_snapshot_id"},
        )

    # Boundary values must agree with the category they are attached to: an
    # "upstream" boundary on category 9 is a contradiction, not a nuance.
    if transport_boundary is not None and category == 4 and transport_boundary != "upstream":
        raise BoundaryAmbiguityError(
            "DC-04: category 4 is upstream transportation and distribution; a "
            f"{transport_boundary!r} boundary contradicts the category",
            details={"control": "DC-04", "category": 4,
                     "field": "transport_boundary", "received": transport_boundary},
        )
    if transport_boundary is not None and category == 9 and transport_boundary != "downstream":
        raise BoundaryAmbiguityError(
            "DC-04: category 9 is downstream transportation and distribution; a "
            f"{transport_boundary!r} boundary contradicts the category",
            details={"control": "DC-04", "category": 9,
                     "field": "transport_boundary", "received": transport_boundary},
        )
    if waste_origin is not None and category == 5 and waste_origin != "operations":
        raise BoundaryAmbiguityError(
            "DC-05: category 5 is waste generated in operations; a "
            f"{waste_origin!r} origin contradicts the category",
            details={"control": "DC-05", "category": 5,
                     "field": "waste_origin", "received": waste_origin},
        )
    if (
        waste_origin is not None
        and category == 12
        and waste_origin != "sold_product_eol"
    ):
        raise BoundaryAmbiguityError(
            "DC-05: category 12 is end-of-life treatment of sold products; a "
            f"{waste_origin!r} origin contradicts the category",
            details={"control": "DC-05", "category": 12,
                     "field": "waste_origin", "received": waste_origin},
        )

