"""P17-IMPLEMENT-07 — the ONE unified Scope 3 calculation service.

Fifteen GHG Protocol categories, **one** accounting pathway. This service is an
orchestrator and validator: it composes the artefacts the architecture already
provides and never re-implements them.

* ``domain/scope3.py`` — taxonomy, architecture status, DC-02/04/05/07 boundary guard.
* ``domain/scope3_contracts.py`` — the explicit per-category contract.
* ``domain/estimation.py`` — T-INV-12 estimation records and the
  no-silent-estimation rule.
* ``domain/data_quality.py`` — the five-value quality vocabulary.
* ``CalculationRequest.from_match_result`` — the canonical bridge (factor selection
  is not duplicated).
* ``CalculationEngine`` — the single canonical write path (snapshot + emissions log).

There is no ``scope3_calculations`` ledger and no per-category engine. Category
identity travels on ``AccountingDimensions.scope3_category`` into the existing
P17 columns, so a Scope 3 result is persisted by exactly the same code as Scope 1
and Scope 2.

Two outcomes, never a third
---------------------------
``CALCULATED`` — the claim was validated and persisted.

``CLARIFICATION_REQUIRED`` — required input is absent. The service returns the
missing field names and guidance and **invents nothing**. Manual review is a
controlled success path, not an error: the caller receives an actionable gap.

Scope 3 is also the only place a value may be an *estimate presented as an
estimate*. The service refuses an estimation pathway labelled with measured data,
and refuses an estimated classification without a persisted ``EstimationRecord``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Optional

from core.exceptions import (
    AccountingDimensionError,
    EstimationRecordRequiredError,
    Scope3CategoryRequiredError,
)
from core.logging import get_logger
from domain.accounting_dimensions import AccountingDimensions
from domain.calculation import CalculationResult
from domain.data_quality import is_estimated, validate_data_quality
from domain.estimation import EstimationRecord
from domain.matching import MatchResult
from domain.scope3 import (
    assert_boundary_complete,
    validate_scope3_category,
)
from domain.scope3_contracts import (
    CategoryPathway,
    ClarificationRequirement,
    Scope3CategoryContract,
    contract_for,
)
from engines.calculation import CalculationEngine, CalculationRequest

logger = get_logger(__name__)

#: The RC2 emissions scope label for every Scope 3 result.
SCOPE3 = "Scope 3"

__all__ = ["Scope3Input", "Scope3Outcome", "Scope3CalculationService", "SCOPE3"]

CALCULATED = "CALCULATED"
CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class Scope3Input:
    """One Scope 3 calculation request, already resolved by the caller.

    ``category`` is required with no default: a Scope 3 figure cannot exist
    without stating which of the fifteen categories it belongs to.
    """

    organization_id: str
    category: int
    quantity: Decimal
    quantity_unit: str
    date: date
    reporting_year: int
    activity: str
    activity_type: str
    #: The Phase 4 matching output. Required for the activity/factor pathway;
    #: optional for an estimation pathway.
    match: Optional[MatchResult] = None
    #: Which pathway the caller is using. Defaults to the contract's adopted one.
    pathway: Optional[str] = None
    methodology: Optional[str] = None
    data_quality: Optional[str] = None
    #: Category-specific required/optional inputs, validated against the contract
    #: (e.g. material, treatment_route, trip_purpose, use_phase_assumption).
    inputs: Mapping[str, Any] = field(default_factory=dict)
    #: DC-02 / DC-04 / DC-05 / DC-07 boundary declarations.
    transport_boundary: Optional[str] = None
    waste_origin: Optional[str] = None
    consolidation_approach: Optional[str] = None
    source_snapshot_id: Optional[str] = None
    facility_id: Optional[str] = None
    supplier_id: Optional[str] = None
    source_item_id: Optional[str] = None
    source_line_item_id: Optional[str] = None
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    #: P17 attribution.
    performed_by: Optional[str] = None
    performed_by_organization_id: Optional[str] = None
    acting_for_organization_id: Optional[str] = None
    #: T-INV-12 — required whenever the value is an estimate.
    estimation: Optional[EstimationRecord] = None
    log_id: Optional[str] = None
    asset_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Scope3Outcome:
    """The result of a Scope 3 request: calculated, or a controlled clarification."""

    status: str
    contract: Scope3CategoryContract
    result: Optional[CalculationResult] = None
    clarification: Optional[ClarificationRequirement] = None

    @property
    def calculated(self) -> bool:
        """True when the claim was validated and persisted."""
        return self.status == CALCULATED


class Scope3CalculationService:
    """Validates and executes a Scope 3 calculation through the canonical path.

    Args:
        engine: The existing :class:`CalculationEngine`. This service performs no
            arithmetic and no persistence of its own.
    """

    def __init__(self, engine: CalculationEngine) -> None:
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine

    @property
    def engine(self) -> CalculationEngine:
        """The canonical engine this service delegates to."""
        return self._engine

    async def calculate(self, request: Scope3Input) -> Scope3Outcome:
        """Validate, calculate and persist one Scope 3 result.

        Returns a ``CLARIFICATION_REQUIRED`` outcome when required input is absent.
        Raises for input that is *present but invalid* — an unknown category, an
        unsupported methodology, a boundary contradiction, an estimation pathway
        claiming measured data, or a missing estimation record — because those are
        defects, not gaps.
        """
        contract = self.contract_for_request(request)

        missing = self.missing_inputs(request, contract)
        if missing:
            logger.info(
                "scope3 clarification required: category=%s missing=%s",
                contract.category,
                ",".join(missing),
            )
            return Scope3Outcome(
                status=CLARIFICATION_REQUIRED,
                contract=contract,
                clarification=self.clarification(request, contract, missing),
            )

        dimensions = self.build_dimensions(request, contract)
        calculation = self.build_request(request, dimensions)
        result = await self._engine.calculate(calculation)
        logger.info(
            "scope3 calculation completed: category=%s pathway=%s quality=%s "
            "organization=%s snapshot=%s",
            contract.category,
            contract.pathway.value,
            request.data_quality,
            request.organization_id,
            result.snapshot.id,
        )
        return Scope3Outcome(status=CALCULATED, contract=contract, result=result)

    def contract_for_request(self, request: Scope3Input) -> Scope3CategoryContract:
        """Resolve the contract, refusing an unknown category or pathway."""
        validate_scope3_category(request.category)
        contract = contract_for(request.category)
        if request.pathway is not None:
            try:
                chosen = CategoryPathway(request.pathway)
            except ValueError:
                raise AccountingDimensionError(
                    f"unknown Scope 3 pathway {request.pathway!r}",
                    details={
                        "field": "pathway",
                        "received": request.pathway,
                        "allowed": [p.value for p in contract.allowed_pathways],
                    },
                ) from None
            if chosen not in contract.allowed_pathways:
                raise AccountingDimensionError(
                    f"category {contract.category} does not accept the "
                    f"{chosen.value!r} pathway; allowed: "
                    f"{[p.value for p in contract.allowed_pathways]}",
                    details={
                        "field": "pathway",
                        "category": contract.category,
                        "received": chosen.value,
                        "allowed": [p.value for p in contract.allowed_pathways],
                    },
                )
        if request.methodology is not None and (
            request.methodology not in contract.methodologies
        ):
            raise AccountingDimensionError(
                f"methodology {request.methodology!r} is not supported for Scope 3 "
                f"category {contract.category}; supported: "
                f"{list(contract.methodologies)}",
                details={
                    "field": "methodology",
                    "category": contract.category,
                    "received": request.methodology,
                    "allowed": list(contract.methodologies),
                },
            )
        return contract

    def missing_inputs(
        self, request: Scope3Input, contract: Scope3CategoryContract
    ) -> tuple[str, ...]:
        """Return the required inputs that were not supplied.

        ``activity``, ``quantity`` and ``unit`` map to the top-level request fields;
        every other contract input is looked up in ``request.inputs``. A field whose
        value is ``None`` or blank counts as absent — a blank is not a value.
        """
        supplied: dict[str, Any] = {
            "activity": request.activity,
            "quantity": request.quantity,
            "unit": request.quantity_unit,
        }
        supplied.update(dict(request.inputs))
        missing: list[str] = []
        for name in contract.required_inputs:
            value = supplied.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        # Boundary declarations are required input too (DC-02/04/05/07).
        for name in contract.required_boundary_inputs:
            if getattr(request, name, None) is None:
                missing.append(name)
        return tuple(missing)

    @staticmethod
    def clarification(
        request: Scope3Input,
        contract: Scope3CategoryContract,
        missing: tuple[str, ...],
    ) -> ClarificationRequirement:
        """Build the controlled clarification for an incomplete request."""
        base = (
            "Supply the missing field(s) and resubmit; the platform will not "
            "invent a value for them."
        )
        if contract.manual_review_conditions:
            base = (
                base + " Routes to review: " + "; ".join(contract.manual_review_conditions)
            )
        return ClarificationRequirement(
            category=contract.category,
            category_name=contract.name,
            missing_fields=missing,
            reason=contract.refusal_reason,
            guidance=base,
            pathway=contract.pathway.value,
        )

    def build_dimensions(
        self, request: Scope3Input, contract: Scope3CategoryContract
    ) -> AccountingDimensions:
        """Validate the Scope 3 claim and build its accounting dimensions.

        Order matters: the boundary guard runs before anything is persisted, so a
        result whose category cannot be defended is refused rather than written.
        """
        pathway = (
            CategoryPathway(request.pathway)
            if request.pathway is not None
            else contract.pathway
        )

        # 1. Data quality is mandatory and must come from the frozen vocabulary: an
        #    unclassified Scope 3 figure would present an estimate as an assurance.
        if request.data_quality is None:
            raise AccountingDimensionError(
                f"Scope 3 category {contract.category} requires an explicit "
                "data_quality classification; an unclassified figure cannot be "
                "distinguished from a measured one",
                details={
                    "field": "data_quality",
                    "category": contract.category,
                    "allowed": list(contract.allowed_data_quality),
                },
            )
        quality = validate_data_quality(request.data_quality)

        # 2. An estimation pathway must be LABELLED as an estimate. This is what
        #    stops an estimate being presented as measured data.
        if pathway is CategoryPathway.ESTIMATION and not is_estimated(quality):
            raise AccountingDimensionError(
                f"Scope 3 category {contract.category} uses the estimation pathway, "
                f"so data_quality must be an estimate classification (got "
                f"{quality!r}); an estimated figure must never be presented as "
                "measured",
                details={
                    "field": "data_quality",
                    "category": contract.category,
                    "received": quality,
                    "allowed": list(contract.allowed_data_quality),
                },
            )

        # 3. T-INV-12 — an estimated value carries a persisted estimation record,
        #    whichever pathway produced it.
        if (is_estimated(quality) or contract.requires_estimation_record) and (
            request.estimation is None
        ):
            raise EstimationRecordRequiredError(
                f"Scope 3 category {contract.category} with data_quality "
                f"{quality!r} requires a persisted estimation record naming its "
                "method, inputs and assumptions (T-INV-12)",
                details={
                    "field": "estimation",
                    "category": contract.category,
                    "data_quality": quality,
                },
            )

        # 4. An activity/factor pathway needs a matched factor. An estimation
        #    pathway needs a substantiated basis, and a factor is then optional.
        if pathway is CategoryPathway.ACTIVITY_FACTOR:
            if request.match is None or request.match.status != "matched":
                raise AccountingDimensionError(
                    f"Scope 3 category {contract.category} on the activity/factor "
                    "pathway requires a matched factor",
                    details={
                        "field": "match",
                        "category": contract.category,
                        "status": (
                            None if request.match is None else request.match.status
                        ),
                    },
                )

        # 5. Evidence-bearing categories must carry a source reference.
        if contract.requires_evidence and not any(
            (
                request.source_item_id,
                request.source_line_item_id,
                request.source_snapshot_id,
            )
        ):
            raise AccountingDimensionError(
                f"Scope 3 category {contract.category} requires a source reference "
                "(source_item_id, source_line_item_id or source_snapshot_id)",
                details={"field": "source_item_id", "category": contract.category},
            )

        # 6. DC-02 / DC-04 / DC-05 / DC-07 — the architecture's own boundary guard,
        #    reused unchanged. It refuses an ambiguous or missing boundary, which is
        #    what stops category 4 becoming 9, 5 becoming 12 and 8 becoming 13.
        assert_boundary_complete(
            category=contract.category,
            transport_boundary=request.transport_boundary,
            waste_origin=request.waste_origin,
            consolidation_approach=request.consolidation_approach,
            source_snapshot_id=request.source_snapshot_id,
        )

        return AccountingDimensions(
            scope3_category=contract.category,
            data_quality=quality,
            facility_id=request.facility_id,
            transport_boundary=request.transport_boundary,
            waste_origin=request.waste_origin,
            source_snapshot_id=request.source_snapshot_id,
            performed_by_organization_id=request.performed_by_organization_id,
            acting_for_organization_id=request.acting_for_organization_id,
        )

    # ------------------------------------------------------------------
    # Request assembly — reuses the canonical P16 bridge
    # ------------------------------------------------------------------
    def build_request(
        self, request: Scope3Input, dimensions: AccountingDimensions
    ) -> CalculationRequest:
        """Build the canonical ``CalculationRequest`` for this Scope 3 claim.

        A factor-backed conversion is required on every path: the platform does
        not synthesise an emissions figure from an activity quantity without a
        factor, which is why an estimation request must still supply a match.
        """
        if request.match is None:
            raise AccountingDimensionError(
                "a Scope 3 calculation requires the matched factor that converts "
                "the activity into emissions; supply a match (estimation affects "
                "the ACTIVITY value and its classification, not the arithmetic)",
                details={"field": "match", "category": dimensions.scope3_category},
            )
        return CalculationRequest.from_match_result(
            request.match,
            organization_id=request.organization_id,
            quantity=request.quantity,
            quantity_unit=request.quantity_unit,
            date=request.date,
            reporting_year=request.reporting_year,
            activity=request.activity,
            activity_type=request.activity_type,
            scope=SCOPE3,
            methodology=request.methodology or "direct_multiply",
            source_file=request.source_file,
            source_page=request.source_page,
            log_id=request.log_id,
            asset_id=request.asset_id,
            facility_id=request.facility_id,
            performed_by=request.performed_by,
            accounting_dimensions=dimensions,
            source_item_id=request.source_item_id,
            source_line_item_id=request.source_line_item_id,
        )



