"""P17-IMPLEMENT-07 — the explicit contract for each Scope 3 category.

ONE unified Scope 3 framework. This module adds the *contract* layer that
``domain/scope3.py`` deliberately does not carry: for each of the fifteen GHG
Protocol categories it states which pathway may be used, what input is required,
what data quality is permitted, whether a factor is needed, whether evidence or
an estimation record is mandatory, and — when the input is insufficient — exactly
what must be clarified instead of guessed.

Why a contract layer at all
---------------------------
``domain/scope3.py`` owns the TAXONOMY, the architecture STATUS and the BOUNDARY
controls. It correctly refuses to invent a methodology: ``assert_calculable``
raises for ``NOT_IMPLEMENTED`` and ``DEFERRED`` categories. That guard is **not**
weakened here — it is left intact and its status is reported unchanged.

Instead each category is given an explicit, inspectable **pathway** so a category
with no automated methodology still has a *truthful* route to a result:

* ``ACTIVITY_FACTOR`` — a real activity quantity multiplied by an existing emission
  factor. Measured/declared quality permitted.
* ``ESTIMATION`` — an explicitly-basis-stated estimate. **Must** carry a persisted
  ``EstimationRecord`` and an estimated data quality. Never presented as measured.
* ``MANUAL_REVIEW`` — no automated route exists; the service returns a controlled
  clarification requirement naming the missing inputs. **No number is invented.**

Where a category is ``NOT_IMPLEMENTED`` because a discriminator is missing
(category 2 capitalisation, category 10 processing), the contract makes that
discriminator a **required input** — precisely the fact the taxonomy recorded as
absent — and the architecture status is still reported verbatim, never upgraded.

Boundary and estimation requirements are DERIVED from ``domain/scope3.py`` so the
contract can never disagree with the architecture's own boundary definitions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from domain.data_quality import (
    DATA_QUALITY_VALUES,
    ESTIMATED_DATA_QUALITY,
)
__all__ = [
    "CategoryPathway",
    "ClarificationRequirement",
    "Scope3CategoryContract",
    "CONTRACTS",
    "contract_for",
    "pathway_of",
]

#: Every classification the vocabulary permits (activity/factor pathways).
_ANY_QUALITY: tuple[str, ...] = tuple(DATA_QUALITY_VALUES)

#: Only the three estimate classifications. An estimation pathway must never be
#: labelled as measured data — that misrepresentation is what T-INV-12 forbids.
_ESTIMATED_ONLY: tuple[str, ...] = tuple(
    q for q in DATA_QUALITY_VALUES if q in ESTIMATED_DATA_QUALITY
)


class CategoryPathway(StrEnum):
    """How a category's result may legitimately be produced."""

    ACTIVITY_FACTOR = "activity_factor"
    ESTIMATION = "estimation"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True, slots=True)
class ClarificationRequirement:
    """A controlled, non-fabricating outcome: what must be supplied instead.

    Returned when required input is absent. It names the category, the missing
    fields and the reason, so an operator sees a precise, actionable gap rather
    than an invented number.
    """

    category: int
    category_name: str
    missing_fields: tuple[str, ...]
    reason: str
    guidance: str
    pathway: str

    def as_payload(self) -> dict:
        """Return the API representation."""
        return {
            "status": "CLARIFICATION_REQUIRED",
            "category": self.category,
            "category_name": self.category_name,
            "pathway": self.pathway,
            "missing_fields": list(self.missing_fields),
            "reason": self.reason,
            "guidance": self.guidance,
        }


@dataclass(frozen=True, slots=True)
class Scope3CategoryContract:
    """The explicit accounting contract for one Scope 3 category.

    ``architecture_status`` is verbatim from ``domain/scope3.py`` and is never
    upgraded by this module.
    """

    category: int
    slug: str
    name: str
    architecture_status: str
    pathway: CategoryPathway
    allowed_pathways: tuple[CategoryPathway, ...]
    methodologies: tuple[str, ...]
    required_inputs: tuple[str, ...] = ()
    optional_inputs: tuple[str, ...] = ()
    required_boundary_inputs: tuple[str, ...] = ()
    requires_factor: bool = True
    requires_estimation_record: bool = False
    allowed_data_quality: tuple[str, ...] = _ANY_QUALITY
    requires_evidence: bool = False
    discriminator: str = ""
    manual_review_conditions: tuple[str, ...] = ()
    refusal_reason: str = ""
    automation: str = ""

    @property
    def is_estimation(self) -> bool:
        """True when this contract's adopted pathway is estimation-based."""
        return self.pathway is CategoryPathway.ESTIMATION


_AF = CategoryPathway.ACTIVITY_FACTOR
_EST = CategoryPathway.ESTIMATION


def _boundary_inputs(category: int) -> tuple[str, ...]:
    """Derive the DC-02/04/05/07 fields the category cannot be accounted without.

    Read from ``domain.scope3`` rather than restated, so a change to the
    architecture's boundary table flows through automatically and the contract
    can never contradict it.
    """
    from domain.scope3 import (
        categories_requiring_consolidation,
        categories_requiring_transport_boundary,
        categories_requiring_waste_origin,
        derives_from_source_snapshot,
    )

    fields: list[str] = []
    if category in categories_requiring_transport_boundary():
        fields.append("transport_boundary")
    if category in categories_requiring_waste_origin():
        fields.append("waste_origin")
    if category in categories_requiring_consolidation():
        fields.append("consolidation_approach")
    if derives_from_source_snapshot(category):
        fields.append("source_snapshot_id")
    return tuple(fields)


#: Per-category specification. Name, slug and architecture status are DERIVED
#: from ``domain.scope3``; boundary inputs are derived from its DC controls. Only
#: the pathway, inputs and guidance are stated here, so the contract cannot drift
#: from the taxonomy.
_SPEC: tuple[dict, ...] = (
    {
        "c": 1, "path": _AF, "also": (_EST,),
        "methods": ("supplier_specific", "average_data", "spend_based"),
        "req": ("activity", "quantity", "unit"), "opt": ("supplier_id", "facility_id"),
        "disc": "consumed in-year (1) vs capitalised (2); capitalisation is a "
                "required declaration, never inferred from the shared factor family",
        "manual": ("spend-based selected without a spend-based factor",),
        "refusal": "an emission factor or a substantiated estimate is required",
        "auto": "activity/factor, with an explicitly-selected spend-based variant",
    },
    {
        "c": 2, "path": _AF, "also": (_EST,),
        "methods": ("supplier_specific", "average_data"),
        "req": ("activity", "quantity", "unit", "capitalisation_declared"),
        "disc": "capitalised (2) vs consumed in-year (1). The taxonomy records "
                "NOT_IMPLEMENTED because capitalisation was not carried by the "
                "product model; this contract makes it a REQUIRED input — the "
                "missing discriminator itself. The status is NOT upgraded.",
        "manual": ("capitalisation not explicitly declared",),
        "refusal": "capitalisation must be explicitly declared; the factor family "
                   "is shared with category 1 and cannot discriminate",
        "auto": "activity/factor, gated on an explicit capitalisation declaration",
    },
    {
        "c": 3, "path": _AF, "also": (),
        "methods": ("average_data", "supplier_specific"),
        "req": ("activity", "quantity", "unit"), "evidence": True,
        "disc": "DC-02: a DERIVATION from an existing Scope 1/2 snapshot (upstream "
                "WTT/T&D only). It must never re-add the Scope 1 fuel quantity or "
                "the Scope 2 energy quantity itself.",
        "manual": ("no upstream source snapshot referenced",),
        "refusal": "DC-02 requires the source Scope 1/2 snapshot id",
        "auto": "activity/factor, hard-linked to its Scope 1/2 source snapshot",
    },
    {
        "c": 4, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "supplier_specific", "distance_based"),
        "req": ("activity", "quantity", "unit"),
        "disc": "DC-04: upstream (paid for by the reporting company). Category 9 is "
                "downstream. Classified by accounting boundary, never by factor family.",
        "refusal": "the transport boundary must be explicitly 'upstream'",
        "auto": "activity/factor on a distance or freight activity",
    },
    {
        "c": 5, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "supplier_specific"),
        "req": ("activity", "quantity", "unit", "material", "treatment_route"),
        "opt": ("supplier_id", "facility_id"),
        "disc": "DC-05: waste arising in operations (5) vs end-of-life of SOLD "
                "products (12). The treatment route must be evidenced.",
        "manual": ("ambiguous treatment route", "unresolved waste supplier"),
        "refusal": "material and an evidenced treatment route are required",
        "auto": "activity/factor reusing the existing waste semantics",
    },
    {
        "c": 6, "path": _AF, "also": (_EST,),
        "methods": ("distance_based", "average_data", "spend_based"),
        "req": ("activity", "quantity", "unit", "trip_purpose"),
        "disc": "trip purpose is recorded on the activity, never inferred from the "
                "travel factor family shared with category 7",
        "refusal": "a travel factor or a substantiated estimate is required",
        "auto": "activity/factor on distance travelled or spend",
    },
    {
        "c": 7, "path": _EST, "also": (_AF,),
        "methods": ("average_data", "extrapolated", "survey_based"),
        "req": ("activity", "quantity", "unit"),
        "disc": "commuting is by definition an average-data estimate unless a survey "
                "supports it; T-INV-12 requires a persisted estimation record",
        "manual": ("no survey or average-data basis recorded",),
        "refusal": "an estimation basis (method plus inputs or assumptions) is "
                   "required; an estimate must never be presented as measured",
        "auto": "estimation-based, explicitly labelled as an estimate",
    },
    {
        "c": 8, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "supplier_specific", "asset_specific"),
        "req": ("activity", "quantity", "unit"),
        "disc": "DC-07: upstream leased assets (8) depend on the consolidation "
                "approach and must not double count an asset already in Scope 1/2. "
                "Category 13 is the downstream mirror.",
        "manual": ("consolidation approach undecided",),
        "refusal": "the organization consolidation approach must be decided (DC-07)",
        "auto": "activity/factor, fails closed without a consolidation approach",
    },
    {
        "c": 9, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "supplier_specific", "distance_based"),
        "req": ("activity", "quantity", "unit"),
        "disc": "DC-04: downstream (paid for by the buyer / after the point of sale). "
                "Category 4 is upstream. Boundary, never factor family.",
        "refusal": "the transport boundary must be explicitly 'downstream'",
        "auto": "activity/factor, distinct from category 4 by persisted boundary",
    },
    {
        "c": 10, "path": _EST, "also": (_AF,),
        "methods": ("average_data", "proxy_data", "modelled"),
        "req": ("activity", "quantity", "unit"),
        "disc": "processing energy/activity of SOLD products by third parties. The "
                "taxonomy records NOT_IMPLEMENTED because no processing-specific "
                "factor family exists; no such factor is invented here.",
        "manual": ("no processing activity evidence",),
        "refusal": "a substantiated processing estimate (or an existing factor for "
                   "the processing activity) is required; processing factors are "
                   "never invented",
        "auto": "estimation-based; uses an existing factor only where one genuinely "
                "applies to the stated processing activity",
    },
    {
        "c": 11, "path": _EST, "also": (_AF,),
        "methods": ("modelled", "average_data", "proxy_data"),
        "req": ("activity", "quantity", "unit", "use_phase_assumption"),
        "opt": ("product_lifetime_years",),
        "disc": "use-phase of sold products. The taxonomy DEFERS the methodology, so "
                "the lifetime/use assumption must be EXPLICITLY supplied and "
                "persisted — it is never silently fabricated.",
        "manual": ("no product lifetime or use-phase assumption provided",),
        "refusal": "an explicit use-phase/lifetime assumption is required; the "
                   "platform will not invent one",
        "auto": "estimation-based over an explicitly persisted assumption set",
    },
    {
        "c": 12, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "supplier_specific"),
        "req": ("activity", "quantity", "unit", "material", "treatment_route"),
        "disc": "DC-05: end-of-life of SOLD products, not operational waste. Not a "
                "clone of category 5: the sold-product origin is persisted as "
                "waste_origin='sold_product_eol'.",
        "manual": ("ambiguous end-of-life route",),
        "refusal": "material composition and an evidenced end-of-life route are "
                   "required",
        "auto": "activity/factor reusing waste semantics with a downstream origin",
    },
    {
        "c": 13, "path": _AF, "also": (_EST,),
        "methods": ("average_data", "asset_specific"),
        "req": ("activity", "quantity", "unit"),
        "disc": "DC-07: downstream leased assets (13) depend on the consolidation "
                "approach and must not double count the same asset period. Category "
                "8 is the upstream mirror.",
        "manual": ("lessor/consolidation record missing",),
        "refusal": "the consolidation approach and lessor record are required (DC-07)",
        "auto": "activity/factor, fails closed without a consolidation approach",
    },
    {
        "c": 14, "path": _EST, "also": (),
        "methods": ("average_data", "extrapolated", "industry_average"),
        "req": ("activity", "quantity", "unit", "allocation_basis"),
        "disc": "franchise-owned sites overlap Scope 1/2 for the reporting company. "
                "The taxonomy DEFERS the operating model, so the allocation basis "
                "must be explicitly recorded rather than assumed.",
        "manual": ("franchise allocation basis not stated",),
        "refusal": "an explicit allocation basis is required; the franchise "
                   "operating model is deferred and is never assumed",
        "auto": "estimation-based over an explicitly recorded allocation basis",
    },
    {
        "c": 15, "path": _EST, "also": (),
        "methods": ("average_data", "industry_average", "modelled"),
        "req": ("activity", "quantity", "unit", "attribution_basis"),
        "disc": "investments depend on the consolidation approach and the equity-share "
                "boundary. Only the equity-share attribution is supported.",
        "manual": ("attribution basis is not equity share",),
        "refusal": "an explicit attribution basis is required; investment emission "
                   "factors are never invented",
        "auto": "estimation-based, equity-share attribution only",
    },
)


def _build_contracts() -> dict[int, Scope3CategoryContract]:
    """Assemble the contracts, deriving taxonomy facts from ``domain.scope3``."""
    from domain.scope3 import definition_of, requires_estimation_record

    built: dict[int, Scope3CategoryContract] = {}
    for spec in _SPEC:
        category = int(spec["c"])
        definition = definition_of(category)
        pathway = spec["path"]
        # T-INV-12 also marks categories whose adopted architecture path uses
        # estimated data, so a category cannot dodge the estimation record by
        # choosing the activity/factor variant of an estimate-based category.
        estimation_required = (
            pathway is CategoryPathway.ESTIMATION
            or requires_estimation_record(category)
        )
        built[category] = Scope3CategoryContract(
            category=category,
            slug=definition.slug,
            name=definition.name,
            architecture_status=definition.status.value,
            pathway=pathway,
            allowed_pathways=(pathway, *spec.get("also", ())),
            methodologies=tuple(spec["methods"]),
            required_inputs=tuple(spec.get("req", ())),
            optional_inputs=tuple(spec.get("opt", ())),
            required_boundary_inputs=_boundary_inputs(category),
            # An activity/factor pathway needs a factor; an estimation pathway
            # needs a substantiated basis, and the factor is then optional.
            requires_factor=pathway is CategoryPathway.ACTIVITY_FACTOR,
            requires_estimation_record=estimation_required,
            allowed_data_quality=(
                _ESTIMATED_ONLY
                if pathway is CategoryPathway.ESTIMATION
                else _ANY_QUALITY
            ),
            requires_evidence=bool(spec.get("evidence", False)),
            discriminator=spec.get("disc", ""),
            manual_review_conditions=tuple(spec.get("manual", ())),
            refusal_reason=spec.get("refusal", ""),
            automation=spec.get("auto", ""),
        )
    return built


#: category number -> its explicit contract. All fifteen are present.
CONTRACTS: dict[int, Scope3CategoryContract] = _build_contracts()


def contract_for(category: int) -> Scope3CategoryContract:
    """Return the contract for ``category``, raising for an invalid category.

    Every category 1-15 has a contract, so this cannot return ``None``; an
    out-of-range value raises ``Scope3CategoryRequiredError`` via the taxonomy's
    own validator rather than a bespoke error.
    """
    from domain.scope3 import validate_scope3_category

    validate_scope3_category(category)
    return CONTRACTS[int(category)]  # type: ignore[index]


def pathway_of(category: int) -> CategoryPathway:
    """Return the adopted pathway for a category."""
    return contract_for(category).pathway



