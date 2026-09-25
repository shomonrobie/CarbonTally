"""P17 canonical accounting dimensions (IMPLEMENT-04).

The single validated carrier for the P17 accounting-dimension vocabulary that
``calculation_snapshots`` and ``emissions_logs`` both store. Future Scope 2 and
Scope 3 calculation engines populate this object and the canonical write path
persists it; nothing here calculates emissions.

Why this module exists
----------------------
The P17-A migration
(``20261010000000_p17a_accounting_dimensions_and_factor_governance.sql``) adds
the dimension columns and enforces their vocabulary with ``CHECK`` constraints,
including the cross-column rules "Scope 2 requires ``scope2_method``" and
"Scope 3 requires ``scope3_category``". Those constraints are ``NOT VALID`` so
historical rows are exempt while **every new write is enforced**.

Validating in the application *before* the write means an invalid combination is
refused with a clear domain error instead of surfacing a raw database constraint
violation to the user (AGENTS.md §46), and — more importantly — it means the
canonical write can fail **before** persisting anything, so a refused
calculation cannot leave a half-written accounting result behind.

The vocabularies below mirror the database ``CHECK`` constraints exactly. They
are duplicated deliberately: the database remains the authority and this module
is the fail-fast gate in front of it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.exceptions import (
    AccountingDimensionError,
    BoundaryAmbiguityError,
    Scope2MethodRequiredError,
    Scope3CategoryRequiredError,
)

#: ``calc_snapshots_scope2_method_check`` / ``emissions_logs_scope2_method_check``.
SCOPE2_METHODS: frozenset[str] = frozenset({"LOCATION_BASED", "MARKET_BASED"})

#: ``..._scope3_category_check`` — GHG Protocol categories 1-15.
SCOPE3_CATEGORY_MIN = 1
SCOPE3_CATEGORY_MAX = 15

#: ``..._energy_type_check``. ``fuel`` is deliberately absent (ARCH-04 LOW-02):
#: fuel-borne energy is Scope 1/3 and carries NULL here.
ENERGY_TYPES: frozenset[str] = frozenset({"electricity", "heat", "steam", "cooling"})

#: ``..._data_quality_check``. No numeric uncertainty is implied (deferred).
DATA_QUALITY_VALUES: frozenset[str] = frozenset(
    {
        "primary_measured",
        "primary_supplier",
        "secondary_estimated",
        "spend_based_estimated",
        "modelled",
    }
)

#: ``..._transport_boundary_check`` — DC-04 discriminator.
TRANSPORT_BOUNDARIES: frozenset[str] = frozenset({"upstream", "downstream"})

#: ``..._waste_origin_check`` — DC-05 discriminator.
WASTE_ORIGINS: frozenset[str] = frozenset({"operations", "sold_product_eol"})

#: ``..._transport_boundary_scope_check`` — category 4 upstream / 9 downstream.
TRANSPORT_BOUNDARY_CATEGORIES: frozenset[int] = frozenset({4, 9})

#: ``..._waste_origin_scope_check`` — category 5 operations / 12 sold-product EoL.
WASTE_ORIGIN_CATEGORIES: frozenset[int] = frozenset({5, 12})

#: The canonical ``scope`` values the dimension rules key off. The existing
#: emissions model stores scope as a display string, so comparison is
#: case-insensitive and whitespace-tolerant.
_SCOPE2 = "scope 2"
_SCOPE3 = "scope 3"


@dataclass(frozen=True, slots=True)
class AccountingDimensions:
    """The P17 accounting dimensions for one calculation.

    Every field is optional because **unknown is a legitimate value**: a
    dimension that is not known must be left ``None`` rather than guessed. A
    ``None`` is written through as SQL ``NULL``, which the database vocabulary
    explicitly permits ("no method/category recorded"), and is never a
    fabricated default.

    ``performed_by_organization_id`` and ``acting_for_organization_id`` are the
    P17 attribution pair. They are *context*, never an authorization boundary:
    ``calculation_snapshots.organization_id`` / ``emissions_logs.organization_id``
    remain the ownership authority and are never derived from these.

    Column names are taken verbatim from the P17-A migration and match
    ``ACTING_FOR_CARRIERS['calculation_snapshot']`` / ``['emissions_log']`` in
    ``data/accounting_context.py``, so the canonical write and the acting-for
    allowlist can never disagree.
    """

    scope2_method: Optional[str] = None
    scope3_category: Optional[int] = None
    energy_type: Optional[str] = None
    data_quality: Optional[str] = None
    facility_id: Optional[str] = None
    transport_boundary: Optional[str] = None
    waste_origin: Optional[str] = None
    source_snapshot_id: Optional[str] = None
    performed_by_organization_id: Optional[str] = None
    acting_for_organization_id: Optional[str] = None

    def validate_for_scope(self, scope: Optional[str]) -> None:
        """Raise the appropriate P17 error if these dimensions contradict ``scope``.

        Mirrors every dimension ``CHECK`` constraint on ``calculation_snapshots``
        and ``emissions_logs``, so an invalid combination is refused before the
        write rather than by the database during it.
        """
        self._validate_vocabulary()
        self._validate_scope_requirements(scope)
        self._validate_cross_column()

    # ------------------------------------------------------------------
    # Vocabulary
    # ------------------------------------------------------------------
    def _validate_vocabulary(self) -> None:
        if self.scope2_method is not None and self.scope2_method not in SCOPE2_METHODS:
            raise AccountingDimensionError(
                "scope2_method must be one of "
                f"{sorted(SCOPE2_METHODS)} (got {self.scope2_method!r})"
            )
        if self.scope3_category is not None and not (
            SCOPE3_CATEGORY_MIN <= self.scope3_category <= SCOPE3_CATEGORY_MAX
        ):
            raise AccountingDimensionError(
                "scope3_category must be between "
                f"{SCOPE3_CATEGORY_MIN} and {SCOPE3_CATEGORY_MAX} "
                f"(got {self.scope3_category!r})"
            )
        if self.energy_type is not None and self.energy_type not in ENERGY_TYPES:
            raise AccountingDimensionError(
                f"energy_type must be one of {sorted(ENERGY_TYPES)} "
                f"(got {self.energy_type!r})"
            )
        if self.data_quality is not None and self.data_quality not in DATA_QUALITY_VALUES:
            raise AccountingDimensionError(
                f"data_quality must be one of {sorted(DATA_QUALITY_VALUES)} "
                f"(got {self.data_quality!r})"
            )
        if (
            self.transport_boundary is not None
            and self.transport_boundary not in TRANSPORT_BOUNDARIES
        ):
            raise AccountingDimensionError(
                f"transport_boundary must be one of {sorted(TRANSPORT_BOUNDARIES)} "
                f"(got {self.transport_boundary!r})"
            )
        if self.waste_origin is not None and self.waste_origin not in WASTE_ORIGINS:
            raise AccountingDimensionError(
                f"waste_origin must be one of {sorted(WASTE_ORIGINS)} "
                f"(got {self.waste_origin!r})"
            )

    # ------------------------------------------------------------------
    # Scope requirements (the *_required and *_scope_only constraints)
    # ------------------------------------------------------------------
    def _validate_scope_requirements(self, scope: Optional[str]) -> None:
        normalised = (scope or "").strip().lower()
        if normalised == _SCOPE2:
            # calc_snapshots_scope2_method_required: scope <> 'Scope 2' OR
            # scope2_method IS NOT NULL. A Scope 2 result without a method is not
            # a valid accounting result.
            if self.scope2_method is None:
                raise Scope2MethodRequiredError(
                    "a Scope 2 calculation requires scope2_method "
                    "(LOCATION_BASED or MARKET_BASED); refusing to persist an "
                    "unattributed Scope 2 result"
                )
            # calc_snapshots_scope3_category_scope_only: a Scope 2 row must not
            # carry a Scope 3 category.
            if self.scope3_category is not None:
                raise AccountingDimensionError(
                    "scope3_category must not be set on a Scope 2 calculation"
                )
        elif normalised == _SCOPE3:
            if self.scope3_category is None:
                raise Scope3CategoryRequiredError(
                    "a Scope 3 calculation requires scope3_category (1-15); "
                    "refusing to persist an uncategorised Scope 3 result"
                )
            if self.scope2_method is not None:
                raise AccountingDimensionError(
                    "scope2_method must not be set on a Scope 3 calculation"
                )
        else:
            # Scope 1 (and any other scope): neither Scope 2 nor Scope 3 identity
            # may be attached.
            if self.scope2_method is not None:
                raise AccountingDimensionError(
                    "scope2_method is only valid on a Scope 2 calculation"
                )
            if self.scope3_category is not None:
                raise AccountingDimensionError(
                    "scope3_category is only valid on a Scope 3 calculation"
                )

    # ------------------------------------------------------------------
    # Cross-column coherence (DC-04 / DC-05)
    # ------------------------------------------------------------------
    def _validate_cross_column(self) -> None:
        if (
            self.transport_boundary is not None
            and self.scope3_category not in TRANSPORT_BOUNDARY_CATEGORIES
        ):
            raise BoundaryAmbiguityError(
                "transport_boundary requires scope3_category to be 4 (upstream) "
                f"or 9 (downstream); got {self.scope3_category!r}"
            )
        if (
            self.waste_origin is not None
            and self.scope3_category not in WASTE_ORIGIN_CATEGORIES
        ):
            raise BoundaryAmbiguityError(
                "waste_origin requires scope3_category to be 5 (operations) or "
                f"12 (sold_product_eol); got {self.scope3_category!r}"
            )

    def as_columns(self) -> dict[str, Optional[object]]:
        """Return the ten P17 column values for an INSERT/UPDATE."""
        return {
            "scope2_method": self.scope2_method,
            "scope3_category": self.scope3_category,
            "energy_type": self.energy_type,
            "data_quality": self.data_quality,
            "facility_id": self.facility_id,
            "transport_boundary": self.transport_boundary,
            "waste_origin": self.waste_origin,
            "source_snapshot_id": self.source_snapshot_id,
            "performed_by_organization_id": self.performed_by_organization_id,
            "acting_for_organization_id": self.acting_for_organization_id,
        }


def validate_scope_dimensions(
    scope: Optional[str], dimensions: Optional[AccountingDimensions]
) -> None:
    """Validate ``dimensions`` for ``scope``; ``None`` means "no dimensions".

    ``None`` is valid for Scope 1 — a caller that supplies no dimensions writes
    NULL for every P17 column, which preserves pre-P17 behaviour exactly. But a
    Scope 2 or Scope 3 calculation is refused without its required identity,
    because the database would refuse it too and persisting it would be an
    accounting error.
    """
    if dimensions is None:
        normalised = (scope or "").strip().lower()
        if normalised == _SCOPE2:
            raise Scope2MethodRequiredError(
                "a Scope 2 calculation requires scope2_method "
                "(LOCATION_BASED or MARKET_BASED)"
            )
        if normalised == _SCOPE3:
            raise Scope3CategoryRequiredError(
                "a Scope 3 calculation requires scope3_category (1-15)"
            )
        return
    dimensions.validate_for_scope(scope)
