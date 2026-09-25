"""P17 unified Carbon Accounting Management System (CAMS) entry point.

Pure Python. No framework, database or infrastructure imports.

This module exists to make one thing structurally true:

    There is ONE accounting engine.

It serves CarbonTally staff, direct customer organizations, consultant
organizations, consultant client organizations and delegated users through the
same dimension resolution, the same boundary guards and the same lifecycle rules.
Consultants get a portfolio/delegation layer *on top of* this engine — never a
parallel engine, a second Scope 2 path, a duplicated factor-selection rule or a
duplicate evidence model.

Every caller — whatever its persona — resolves its accounting dimensions through
:func:`resolve_accounting_dimensions`, which is the only place the Scope 2,
Scope 3, boundary and estimation rules are combined. A persona may differ in
*what it may ask for*; it cannot differ in *what makes a defensible number*.

Persona-appropriate authorization is applied by the caller before reaching this
module (RLS plus server-side capability checks). Nothing here substitutes for
authorization — and neither does the acting-for context, which is carried for
provenance only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.exceptions import AccountingDimensionError, Scope3CategoryRequiredError

from .acting_for import ActingForContext
from .data_quality import describe_data_quality, is_estimated, validate_data_quality
from .scope2 import assert_scope2_dimensions, validate_energy_type, validate_scope2_method
from .scope3 import (
    assert_boundary_complete,
    assert_calculable,
    definition_of,
    requires_estimation_record,
    validate_scope3_category,
)

__all__ = [
    "AccountingDimensions",
    "CamsPersona",
    "CamsContext",
    "resolve_accounting_dimensions",
    "describe_dimensions",
]


@dataclass(frozen=True, slots=True)
class AccountingDimensions:
    """The persisted dimensions of ONE accounting result.

    Attributes:
        scope: ``Scope 1``, ``Scope 2`` or ``Scope 3``.
        scope2_method: Required for Scope 2 (``LOCATION_BASED``/``MARKET_BASED``).
        scope3_category: Required for Scope 3 (1-15).
        energy_type: Scope 2 energy type (electricity/heat/steam/cooling).
        data_quality: How the value was obtained.
        facility_id: The site the consumption occurred at.
        transport_boundary: DC-04 discriminator for categories 4/9.
        waste_origin: DC-05 discriminator for categories 5/12.
        source_snapshot_id: DC-02 derivation link for category 3.
    """

    scope: Optional[str] = None
    scope2_method: Optional[str] = None
    scope3_category: Optional[int] = None
    energy_type: Optional[str] = None
    data_quality: Optional[str] = None
    facility_id: Optional[str] = None
    transport_boundary: Optional[str] = None
    waste_origin: Optional[str] = None
    source_snapshot_id: Optional[str] = None

    def as_columns(self) -> dict[str, Any]:
        """Return the column payload written to ``calculation_snapshots``.

        The same payload is mirrored onto ``emissions_logs`` so the consumption
        boundary can filter without a join.
        """
        return {
            "scope2_method": self.scope2_method,
            "scope3_category": self.scope3_category,
            "energy_type": self.energy_type,
            "data_quality": self.data_quality,
            "facility_id": self.facility_id,
            "transport_boundary": self.transport_boundary,
            "waste_origin": self.waste_origin,
            "source_snapshot_id": self.source_snapshot_id,
        }

    @property
    def is_estimated(self) -> bool:
        """True when this result's data quality is an estimate."""
        return is_estimated(self.data_quality)


class CamsPersona:
    """Which operating domain a caller belongs to.

    Personas exist for *authorization and presentation*, not for accounting.
    """

    STAFF = "STAFF"
    DIRECT_CUSTOMER = "DIRECT_CUSTOMER"
    CONSULTANT = "CONSULTANT"
    CONSULTANT_CLIENT = "CONSULTANT_CLIENT"
    DELEGATED_USER = "DELEGATED_USER"
    #: Processing Entity staff — a distinct operating domain with its own
    #: boundary; never treated as internal staff and never given customer
    #: organization access by default.
    PROCESSING_ENTITY = "PROCESSING_ENTITY"


@dataclass(frozen=True, slots=True)
class CamsContext:
    """Who is operating, on whose data, and for whom.

    Attributes:
        actor_user_id: The authenticated user.
        data_owning_organization_id: The tenant that OWNS the accounting data.
            This is the authorization key, not the acting-for value.
        acting_for: The persisted acting-for context, or ``None`` when the actor
            is operating as themselves.
        persona: The operating domain, for presentation and capability checks.
    """

    actor_user_id: str
    data_owning_organization_id: str
    acting_for: Optional[ActingForContext] = None
    persona: str = CamsPersona.DIRECT_CUSTOMER

    @property
    def acting_for_organization_id(self) -> Optional[str]:
        """The organization the operation is attributed to, when delegated."""
        return self.acting_for.acting_for_organization_id if self.acting_for else None

    @property
    def is_delegated(self) -> bool:
        """True when the actor is operating for an organization other than their own."""
        return bool(self.acting_for and self.acting_for.is_delegated)

    def provenance_columns(self) -> dict[str, Optional[str]]:
        """Return the acting-for provenance payload for the eight §10.3 paths."""
        if self.acting_for is None:
            return {"actor_organization_id": None,
                    "acting_for_organization_id": None}
        return self.acting_for.as_audit_columns()


def resolve_accounting_dimensions(
    *,
    scope: Optional[str],
    scope2_method: Optional[str] = None,
    scope3_category: Optional[int] = None,
    energy_type: Optional[str] = None,
    data_quality: Optional[str] = None,
    facility_id: Optional[str] = None,
    transport_boundary: Optional[str] = None,
    waste_origin: Optional[str] = None,
    source_snapshot_id: Optional[str] = None,
    consolidation_approach: Optional[str] = None,
    require_calculable_category: bool = True,
) -> AccountingDimensions:
    """Validate and normalise the dimensions of one accounting result.

    The SINGLE place the accounting rules are combined, so every persona reaches
    the same verdict on what a defensible number is. In order:

    1. vocabulary validation for every supplied dimension;
    2. Scope 2 method requirement (``assert_scope2_dimensions``);
    3. Scope 3 category requirement plus the architecture-status guard — a
       ``NOT_IMPLEMENTED`` or ``DEFERRED`` category is refused rather than
       silently calculated;
    4. boundary completeness (DC-02/DC-04/DC-05/DC-07) via ``scope3``;
    5. cross-scope coherence, so a Scope 2 method cannot be attached to a Scope 3
       result or a category to a Scope 2 result.

    It does NOT check estimated-value substantiation: that needs the persisted
    estimation record, which the caller writes alongside the result. Use
    :func:`domain.estimation.requires_estimation_record` for that decision.
    """
    validate_scope2_method(scope2_method)
    validate_scope3_category(scope3_category)
    validate_energy_type(energy_type)
    validate_data_quality(data_quality)

    assert_scope2_dimensions(
        scope=scope, scope2_method=scope2_method, energy_type=energy_type
    )

    if scope == "Scope 3":
        if scope3_category is None:
            raise Scope3CategoryRequiredError(
                "a Scope 3 result must record its GHG Protocol category (1-15); the "
                "category is never inferred from the factor",
                details={"field": "scope3_category"},
            )
        if require_calculable_category:
            assert_calculable(scope3_category)

    # Cross-scope coherence: a dimension attached to the wrong scope is a data
    # defect, not a nuance, because reporting groups by scope.
    if scope2_method is not None and scope != "Scope 2":
        raise AccountingDimensionError(
            f"scope2_method may only be set on a Scope 2 result (scope={scope!r})",
            details={"field": "scope2_method", "scope": scope},
        )
    if scope3_category is not None and scope != "Scope 3":
        raise AccountingDimensionError(
            f"scope3_category may only be set on a Scope 3 result (scope={scope!r})",
            details={"field": "scope3_category", "scope": scope},
        )
    if energy_type is not None and scope != "Scope 2":
        raise AccountingDimensionError(
            f"energy_type may only be set on a Scope 2 result (scope={scope!r}); "
            "fuel-borne energy is Scope 1/3 and carries no energy_type",
            details={"field": "energy_type", "scope": scope},
        )

    assert_boundary_complete(
        category=scope3_category,
        transport_boundary=transport_boundary,
        waste_origin=waste_origin,
        consolidation_approach=consolidation_approach,
        source_snapshot_id=source_snapshot_id,
    )

    return AccountingDimensions(
        scope=scope,
        scope2_method=scope2_method,
        scope3_category=scope3_category,
        energy_type=energy_type,
        data_quality=data_quality,
        facility_id=facility_id,
        transport_boundary=transport_boundary,
        waste_origin=waste_origin,
        source_snapshot_id=source_snapshot_id,
    )


def describe_dimensions(dimensions: AccountingDimensions) -> dict[str, Any]:
    """Return a business-first description of a result's accounting dimensions.

    The UI principle is that operational screens state business meaning rather
    than raw column values, so this returns a human-readable label alongside each
    machine value and names the Scope 3 category rather than printing its number.
    """
    label_parts: list[str] = []
    status: Optional[str] = None
    category_name: Optional[str] = None

    if dimensions.scope:
        label_parts.append(dimensions.scope)
    if dimensions.scope2_method:
        label_parts.append(dimensions.scope2_method.replace("_", " ").title())
    if dimensions.energy_type:
        label_parts.append(dimensions.energy_type.title())
    if dimensions.scope3_category:
        definition = definition_of(dimensions.scope3_category)
        category_name = definition.name
        status = definition.status.value
        label_parts.append(f"Category {definition.category} — {definition.name}")

    return {
        "label": " · ".join(label_parts) if label_parts else "Dimensions not recorded",
        "scope": dimensions.scope,
        "scope2_method": dimensions.scope2_method,
        "scope3_category": dimensions.scope3_category,
        "scope3_category_name": category_name,
        "scope3_status": status,
        "energy_type": dimensions.energy_type,
        "data_quality": dimensions.data_quality,
        "data_quality_description": describe_data_quality(dimensions.data_quality),
        "facility_id": dimensions.facility_id,
        "transport_boundary": dimensions.transport_boundary,
        "waste_origin": dimensions.waste_origin,
        "source_snapshot_id": dimensions.source_snapshot_id,
        "is_estimated": dimensions.is_estimated,
        "requires_estimation_record": requires_estimation_record(
            dimensions.scope3_category
        ),
    }
