"""P17 Scope 2 calculation service (IMPLEMENT-05).

The vertical slice that turns a Scope 2 activity input into a calculated,
attributed, persisted emissions result through the canonical accounting write
pipeline completed in IMPLEMENT-04.

What this module is
-------------------
An **orchestrator and validator**, not a calculation engine and not a factor
matcher. It composes the pieces the architecture already provides:

* :mod:`domain.scope2` — method / energy-type vocabulary, ``fuel`` rejection,
  instrument eligibility rules, ``assert_scope2_dimensions``.
* :mod:`domain.contractual_instruments` — the instrument + allocation domain and
  the DC-09 over-allocation guard.
* the existing Phase 4 matching output (``MatchResult``) and
  ``CalculationRequest.from_match_result`` — so **factor selection is not
  duplicated**.
* ``CalculationEngine.calculate()`` — the single canonical write path, so
  **there is no second calculation engine and no second persistence system**.

Scope 2 is deliberately strict about one thing above all others: **the method is
never inferred**. A location-based and a market-based figure are different
accounting claims, not two views of one number, so a Scope 2 calculation without
an explicit method is refused (``Scope2MethodRequiredError``) and a market-based
request is **never silently downgraded** to location-based when its instrument is
missing or ineligible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

from core.exceptions import (
    AccountingDimensionError,
    InstrumentEligibilityError,
)
from core.logging import get_logger
from domain.accounting_dimensions import AccountingDimensions
from domain.calculation import CalculationResult
from domain.contractual_instruments import (
    ContractualInstrument,
    InstrumentAllocation,
    assert_allocation_within_quantity,
    remaining_quantity,
)
from domain.matching import MatchResult
from domain.scope2 import (
    EnergyType,
    Scope2Method,
    assert_scope2_dimensions,
    requires_instrument,
    validate_energy_type,
    validate_scope2_method,
)
from engines.calculation import CalculationEngine, CalculationRequest

logger = get_logger(__name__)

#: The scope label every Scope 2 result carries. This is the existing RC2
#: emissions ``scope`` string, not a new vocabulary.
SCOPE2 = "Scope 2"

__all__ = ["Scope2Input", "Scope2CalculationService", "SCOPE2"]


@dataclass(frozen=True, slots=True)
class Scope2Input:
    """One Scope 2 calculation request, already resolved by the caller.

    ``method`` and ``energy_type`` are REQUIRED positional-style fields with no
    default: there is no way to construct a Scope 2 input while omitting the
    accounting method, which is the structural half of "never infer the method".

    ``match`` is the Phase 4 matching output. Supplying the matching result
    rather than a factor id is deliberate: it guarantees the factor arrived
    through the existing matching infrastructure (customer-factor precedence
    included) and that the snapshot's ``request_id`` remains the P16
    deterministic request identity.

    Tenant context: ``organization_id`` is the **data owner**. The
    acting-for/performed-by pair is carried separately and is never derived from
    the owner (and vice versa) — see :class:`AccountingDimensions`.
    """

    organization_id: str
    quantity: Decimal
    quantity_unit: str
    date: date
    reporting_year: int
    activity: str
    activity_type: str
    method: str
    energy_type: str
    match: MatchResult
    #: Consumption geography, used for the Scope 2 location/market geography
    #: checks. When omitted the factor's own country is used, so a single-geography
    #: dataset needs no extra field.
    geography: Optional[str] = None
    data_quality: Optional[str] = None
    facility_id: Optional[str] = None
    #: The authorized supplier attribution for this energy activity
    #: (P17-IMPLEMENT-09) — the utility or energy supplier the consumption came
    #: from. ``None`` stays NULL: an unresolved supplier is never invented. The
    #: route proves ownership against the data owner before the value reaches here.
    supplier_id: Optional[str] = None
    #: P17-IMPLEMENT-10 / P17-PRODUCT-01 §5 — the purchase channel (broker or
    #: intermediary), kept strictly apart from ``supplier_id``. ``None`` stays
    #: NULL and is never back-filled from the supplier.
    transaction_provider: Optional[str] = None
    source_item_id: Optional[str] = None
    source_line_item_id: Optional[str] = None
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    #: P17 attribution. ``performed_by`` is the human/entity actor label already
    #: supported by the engine; the two organization fields are the P17 pair.
    performed_by: Optional[str] = None
    performed_by_organization_id: Optional[str] = None
    acting_for_organization_id: Optional[str] = None
    #: MARKET_BASED only: the contractual instrument being claimed and the
    #: quantity of it allocated to this consumption row.
    instrument: Optional[ContractualInstrument] = None
    allocated_quantity: Optional[Decimal] = None
    #: Allocations already recorded against ``instrument``, used by the DC-09
    #: guard so the same instrument quantity cannot be claimed twice.
    existing_allocations: Sequence[InstrumentAllocation] = field(default_factory=tuple)
    log_id: Optional[str] = None
    asset_id: Optional[str] = None


class Scope2CalculationService:
    """Validates and executes a Scope 2 calculation through the canonical path.

    Args:
        engine: The existing :class:`CalculationEngine`. This service never
            computes emissions itself — it validates the accounting claim and
            delegates the arithmetic and persistence to the engine.
    """

    def __init__(self, engine: CalculationEngine) -> None:
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine

    @property
    def engine(self) -> CalculationEngine:
        """The canonical engine this service delegates to."""
        return self._engine

    async def calculate(self, request: Scope2Input) -> CalculationResult:
        """Validate, calculate and persist one Scope 2 result."""
        dimensions = self.build_dimensions(request)
        calculation = self.build_request(request, dimensions)
        result = await self._engine.calculate(calculation)
        logger.info(
            "scope2 calculation completed: method=%s energy_type=%s "
            "organization=%s acting_for=%s snapshot=%s",
            dimensions.scope2_method,
            dimensions.energy_type,
            request.organization_id,
            dimensions.acting_for_organization_id,
            result.snapshot.id,
        )
        return result

    # ------------------------------------------------------------------
    # Validation + dimension assembly
    # ------------------------------------------------------------------
    def build_dimensions(self, request: Scope2Input) -> AccountingDimensions:
        """Validate the Scope 2 claim and build its accounting dimensions."""
        # 1. The method is explicit and valid. ``validate_scope2_method`` refuses
        #    an unknown method; ``assert_scope2_dimensions`` refuses a missing one.
        assert_scope2_dimensions(
            scope=SCOPE2, scope2_method=request.method, energy_type=request.energy_type
        )
        method = validate_scope2_method(request.method)
        energy_type = validate_energy_type(request.energy_type)

        # 2. Factor governance — the factor must be a Scope 2 factor for the
        #    requested year and, where both sides state one, geography.
        self._assert_factor_governs_scope2(request)

        # 3. Method-specific instrument handling. This is where a market-based
        #    request is refused rather than quietly downgraded.
        if requires_instrument(method):
            self._validate_market_based(request, method)
        else:
            self._assert_no_instrument_for_location_based(request)

        return AccountingDimensions(
            scope2_method=method,
            energy_type=energy_type,
            data_quality=request.data_quality,
            facility_id=request.facility_id,
            # The attribution pair. ``organization_id`` stays the owner and is
            # never taken from these.
            performed_by_organization_id=request.performed_by_organization_id,
            acting_for_organization_id=request.acting_for_organization_id,
            # P17-IMPLEMENT-10 — the purchase channel (P17-PRODUCT-01 §5). Carried
            # through unchanged: it is not a supplier reference and is never
            # derived from one. No ``scope3_method``: that dimension is
            # Scope-3-only and the domain refuses it on a Scope 2 result.
            transaction_provider=request.transaction_provider,
        )

    def _factor(self, request: Scope2Input):
        """The factor this calculation will use, or ``None`` for customer factors."""
        if request.match.factor_kind == "customer_factor":
            return None
        return request.match.factor

    def _assert_factor_governs_scope2(self, request: Scope2Input) -> None:
        """Refuse a factor that is not a valid Scope 2 factor for this claim.

        An approved customer factor is exempt from the CarbonTally scope/year
        checks: it is the organization's own contracted value (P16 factor
        precedence — an APPROVED CUSTOMER FACTOR beats CarbonTally matching) and
        it is not an ``emission_factors`` row, so it carries no CarbonTally scope
        or reporting year to compare against.
        """
        if request.match.status != "matched":
            raise AccountingDimensionError(
                "a Scope 2 calculation requires a matched factor",
                details={"status": request.match.status},
            )
        factor = self._factor(request)
        if factor is None:
            return
        if factor.scope != SCOPE2:
            raise AccountingDimensionError(
                f"factor {factor.id} is declared {factor.scope!r}; a Scope 2 "
                "calculation must not use a factor from another scope",
                details={
                    "field": "scope",
                    "factor_id": factor.id,
                    "factor_scope": factor.scope,
                },
            )
        if factor.reporting_year != request.reporting_year:
            raise AccountingDimensionError(
                f"factor {factor.id} is a {factor.reporting_year} factor but the "
                f"calculation is for {request.reporting_year}; another factor year "
                "is never silently substituted",
                details={
                    "field": "reporting_year",
                    "factor_id": factor.id,
                    "factor_year": factor.reporting_year,
                    "requested_year": request.reporting_year,
                },
            )
        geography = request.geography or factor.country
        if geography and factor.country and factor.country != geography:
            raise AccountingDimensionError(
                f"factor {factor.id} is for {factor.country!r} but the consumption "
                f"geography is {geography!r}",
                details={
                    "field": "geography",
                    "factor_id": factor.id,
                    "factor_country": factor.country,
                    "consumption_geography": geography,
                },
            )

    def _validate_market_based(self, request: Scope2Input, method: Optional[str]) -> None:
        """DC-09 / ARCH-04 — a market-based claim must be backed by an instrument.

        Every refusal here is explicit. A market-based calculation with no
        instrument, an ineligible instrument, or insufficient allocation is
        **refused**, never recomputed as location-based: silently substituting the
        grid-average figure would replace the claim the caller asked for with a
        different one.
        """
        instrument = request.instrument
        if instrument is None:
            raise InstrumentEligibilityError(
                "a MARKET_BASED Scope 2 calculation requires a contractual "
                "instrument; the grid-average figure is a different claim and is "
                "never substituted automatically",
                details={"field": "instrument", "method": method},
            )
        # Tenant isolation: the instrument must belong to the data-owning
        # organization. An instrument from another tenant is refused outright —
        # acting-for context is never an entitlement.
        if instrument.organization_id != request.organization_id:
            raise AccountingDimensionError(
                "the contractual instrument belongs to a different organization "
                "than the calculation's data owner",
                details={
                    "field": "instrument.organization_id",
                    "instrument_organization_id": instrument.organization_id,
                    "calculation_organization_id": request.organization_id,
                },
            )
        # Eligibility: active, market-based, geography and vintage compatible.
        consumption_geography = request.geography or instrument.geography
        instrument.assert_can_support(
            method=method,
            consumption_geography=consumption_geography,
            consumption_vintage_year=request.reporting_year,
            instrument_method=method,
        )
        # Allocation must be stated and must cover the consumption claimed.
        if request.allocated_quantity is None:
            raise InstrumentEligibilityError(
                "a MARKET_BASED Scope 2 calculation must state the quantity of the "
                "instrument allocated to it",
                details={
                    "field": "allocated_quantity",
                    "instrument_id": instrument.identifier,
                    "unallocated": str(
                        remaining_quantity(instrument, request.existing_allocations)
                    ),
                },
            )
        if request.allocated_quantity != request.quantity:
            raise InstrumentEligibilityError(
                "the instrument allocation must equal the consumption quantity; a "
                "partial allocation cannot support a full market-based claim",
                details={
                    "field": "allocated_quantity",
                    "allocated": str(request.allocated_quantity),
                    "quantity": str(request.quantity),
                },
            )
        # DC-09 — the instrument quantity cannot be claimed more than once. The
        # unit is checked too, so 500 kWh cannot be allocated against a 500 MWh
        # instrument.
        assert_allocation_within_quantity(
            instrument=instrument,
            existing=request.existing_allocations,
            new_quantity=request.allocated_quantity,
            unit=request.quantity_unit,
        )

    @staticmethod
    def _assert_no_instrument_for_location_based(request: Scope2Input) -> None:
        """Refuse an instrument attached to a location-based claim.

        ``instrument_is_eligible`` already returns False for a non-market-based
        method; failing here means the caller is told plainly rather than having
        the instrument silently ignored.
        """
        if request.instrument is not None:
            raise InstrumentEligibilityError(
                "a contractual instrument cannot support a LOCATION_BASED Scope 2 "
                "result; location-based accounting is a claim about the grid",
                details={"field": "instrument"},
            )

    # ------------------------------------------------------------------
    # Request assembly — reuses the canonical P16 bridge
    # ------------------------------------------------------------------
    def build_request(
        self, request: Scope2Input, dimensions: AccountingDimensions
    ) -> CalculationRequest:
        """Build the canonical ``CalculationRequest`` for this Scope 2 claim."""
        return CalculationRequest.from_match_result(
            request.match,
            organization_id=request.organization_id,
            quantity=request.quantity,
            quantity_unit=request.quantity_unit,
            date=request.date,
            reporting_year=request.reporting_year,
            activity=request.activity,
            activity_type=request.activity_type,
            scope=SCOPE2,
            source_file=request.source_file,
            source_page=request.source_page,
            log_id=request.log_id,
            asset_id=request.asset_id,
            facility_id=request.facility_id,
            performed_by=request.performed_by,
            accounting_dimensions=dimensions,
            # P17-IMPLEMENT-09 — supplier attribution on the Scope 2 path, so a
            # utility/supplier-specific figure is attributable to the supplier it
            # came from rather than being recorded as an unattributed total.
            supplier_id=request.supplier_id,
        )


