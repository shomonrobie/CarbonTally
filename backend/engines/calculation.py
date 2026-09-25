"""Emissions Calculation Engine (Backend v2.1 §13, prep-pack Phase 6).

Reproducible CO2e calculations with immutable snapshots. The engine:

* **consumes the Phase 4 Matching Engine output** — it receives the matched
  :class:`domain.factor.EmissionFactor` (via :class:`CalculationRequest`,
  optionally built from a :class:`domain.matching.MatchResult`) and never
  performs factor matching itself;
* **never touches the database directly** — snapshot and emissions-log
  persistence go through the repository layer (:class:`CalculationSink`);
* applies the factor exactly (unit-match validation, ``RESULT_PRECISION``
  quantisation), builds a :class:`domain.calculation.CalculationSnapshot` with
  a SHA-256 content hash, persists it, publishes the workflow events and
  records the audit entry (CT-ARCH-014);
* exposes :meth:`verify` for audit-time reproducibility checks
  (:class:`domain.calculation.VerificationResult`).

Dependency rules: this module imports from ``core`` (errors), ``domain``
(calculation + factor + matching contracts + events) and ``infra`` (event bus,
audit logger). It is stateless per request — the composition root creates a new
engine per request.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import date as _Date, datetime, timezone
from decimal import Decimal
from typing import Optional, Protocol

from core.exceptions import UnitMismatchError, ValidationFailedError
from core.logging import get_logger
from core.units import is_currency_unit, resolve_unit_for_factor
from domain.accounting_dimensions import (
    AccountingDimensions,
    validate_scope_dimensions,
)
from domain.calculation import (
    CalculationMethodology,
    CalculationResult,
    CalculationSnapshot,
    EmissionLog,
    VerificationResult,
)
from domain.customer_factor import CustomerFactor
from domain.factor import RESULT_PRECISION, EmissionFactor
from domain.matching import MatchResult
from domain.workflow import CalculationCompleted, CalculationRequested, DomainEvent
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)

#: Default algorithm version stamped into every snapshot (configurable).
DEFAULT_ALGORITHM_VERSION = "v1.0"

#: Tonnes conversion precision (kg -> tonnes, 6 decimal places).
_TONNES_PRECISION = Decimal("0.000001")

#: Internal factor-matching / methodology labels that must never reach the
#: public CalculationMethodology contract. They are implementation details of
#: the matching stage names / factor kinds and are derived server-side into a
#: canonical methodology before persistence (P0-3).
_INTERNAL_METHODOLOGY_LABELS: frozenset[str] = frozenset(
    {
        "customer_factor",
        "keyword_search",
        "exact_match",
        "natural_key",
        "alias",
        "fuzzy",
        "semantic",
        "provider",
    }
)


def derive_methodology(
    value: str,
    *,
    is_customer_factor: bool,
    quantity_unit: Optional[str],
) -> Optional[str]:
    """Map an internal methodology label to a canonical CalculationMethodology.

    Returns ``None`` when ``value`` is neither a canonical methodology value
    (handled by the caller) nor a known internal label — the caller then fails
    safely (invalid methodology values are never silently accepted).

    Derivation is deterministic and mirrors the automatic-pipeline rule:
    * a customer factor with a currency unit is ``spend_based``;
    * a distance unit (km / miles) is ``distance_based``;
    * everything else is ``direct_multiply``.
    """
    if value not in _INTERNAL_METHODOLOGY_LABELS:
        return None
    unit = str(quantity_unit or "").strip()
    if is_customer_factor and is_currency_unit(unit):
        return CalculationMethodology.SPEND_BASED.value
    if unit.lower() in ("km", "miles", "mile"):
        return CalculationMethodology.DISTANCE_BASED.value
    return CalculationMethodology.DIRECT_MULTIPLY.value


#: P17-IMPLEMENT-10 — product category methodology (P17-PRODUCT-01 §29/§34) to
#: the ENGINE arithmetic label that describes how the number was computed.
#:
#: These are two different facts and both are persisted: the product method goes
#: to ``scope3_method`` (the accounting claim) and the arithmetic label goes to
#: ``methodology`` (the calculation). The Scope 2 path already works this way —
#: ``scope2_method`` carries LOCATION_BASED/MARKET_BASED while ``methodology``
#: stays ``direct_multiply``.
#:
#: Only the two product methods that genuinely change the arithmetic have their
#: own label. Every other product method (``supplier_specific``, ``average_data``,
#: ``extrapolated``, ``survey_based``, ``asset_specific``, ``industry_average``,
#: ``modelled``, ``proxy_data``) computes ``quantity x factor``, so the honest
#: arithmetic label is ``direct_multiply`` — the distinction that matters between
#: those methods lives in ``scope3_method`` and in the persisted estimation
#: record, not in the multiplication.
_ENGINE_METHODOLOGY_BY_PRODUCT_METHOD: dict[str, CalculationMethodology] = {
    "spend_based": CalculationMethodology.SPEND_BASED,
    "distance_based": CalculationMethodology.DISTANCE_BASED,
}


def engine_methodology_for(
    scope3_method: Optional[str],
) -> Optional[CalculationMethodology]:
    """Return the ENGINE arithmetic label for a product category methodology.

    ``None`` (no method recorded) returns ``None`` — the caller keeps the
    existing default rather than this function inventing one. The mapping is
    total for a supplied value: a product method that does not change the
    arithmetic is explicitly ``DIRECT_MULTIPLY``, which is the documented,
    tested projection, not a silent fallback.
    """
    if scope3_method is None:
        return None
    return _ENGINE_METHODOLOGY_BY_PRODUCT_METHOD.get(
        scope3_method, CalculationMethodology.DIRECT_MULTIPLY
    )



class CalculationSink(Protocol):
    """The repository surface the engine persists through.

    Satisfied structurally by
    :class:`data.emissions_logs.EmissionsLogsRepository` (the prep-pack-
    designated snapshots repo). Never reached directly by the engine — all
    persistence goes through this protocol.
    """

    async def save_snapshot(
        self,
        snapshot: CalculationSnapshot,
        *,
        activity: str,
        activity_type: str,
        factor_source: Optional[str] = None,
        factor_set: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        calculated_by: Optional[str] = None,
        factor_kind: Optional[str] = None,
        customer_factor_id: Optional[str] = None,
    ) -> CalculationSnapshot: ...

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: _Date,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
        supplier_id: Optional[str] = None,
        accounting_dimensions: Optional[AccountingDimensions] = None,
    ) -> EmissionLog: ...

    async def save(self, entity: EmissionLog) -> EmissionLog: ...


@dataclasses.dataclass(frozen=True, slots=True)
class CalculationRequest:
    """Input contract for the Calculation Engine.

    ``factor`` is the Phase 4 matching output for CarbonTally-managed factors;
    ``customer_factor`` is the matched approved customer factor (D-cf-5 /
    ADR-V3-002). Exactly one of the two is set — the snapshot provenance
    (O1 / ADR-V3-014) is recorded via ``factor_kind`` +
    ``customer_factor_id``. ``match_request_id`` is the id of the Phase 4
    :class:`domain.matching.MatchRequest` that produced the match. When a
    ``log_id`` is supplied the engine updates that existing ``emissions_logs``
    row; otherwise it creates one.
    """

    match_request_id: str
    organization_id: str
    quantity: Decimal
    quantity_unit: str
    date: _Date
    reporting_year: int
    activity: str
    activity_type: str
    scope: Optional[str] = None
    #: P17-IMPLEMENT-04 — the canonical accounting dimensions for this
    #: calculation (Scope 2 method, Scope 3 category, energy type, data quality,
    #: facility, boundary discriminators, derivation lineage) plus the
    #: acting-for/performed-by attribution pair.
    #:
    #: ``None`` means "no dimensions supplied": the P17 columns are written NULL,
    #: which is exactly pre-P17 behaviour. A Scope 2 or Scope 3 calculation must
    #: supply its required identity — :func:`validate_scope_dimensions` refuses
    #: it otherwise, before any write, because the database enforces the same
    #: rule on new rows and a fabricated method/category would be an invented
    #: accounting claim.
    accounting_dimensions: Optional[AccountingDimensions] = None
    methodology: str = CalculationMethodology.DIRECT_MULTIPLY.value
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    source_item_id: Optional[str] = None
    #: Phase 8 B2 §13.1 — the addressable source LINE id resolved from
    #: ``(source_item_id, ordinal)`` by the calculation caller. Optional and
    #: insert-time only: when no materialised line exists the value is ``None``
    #: (NULL is the honesty mechanism, §8.2) and it is never part of the
    #: content-hash inputs or the request-id derivation for existing snapshots
    #: (§8.4, §13.3).
    source_line_item_id: Optional[str] = None
    #: Actual human actor (auth.users id — CarbonTally internal staff or
    #: Processing-Entity staff) who requested the calculation. Persisted on the
    #: immutable snapshot as ``calculation_snapshots.performed_by``. ``None``
    #: for automatic-pipeline runs (machine provenance is out of scope); the
    #: organisation context is always carried separately by
    #: ``organization_id`` / the snapshot's ``calculated_by``.
    performed_by: Optional[str] = None
    log_id: Optional[str] = None
    asset_id: Optional[str] = None
    facility_id: Optional[str] = None
    #: P12-IMPL-02 §E — the operator-resolved supplier carried from
    #: ``manual_extraction_items.mapped_supplier_id`` (Decision-01 sole source of
    #: truth) into ``emissions_logs.supplier_id`` so downstream evidence/Insight
    #: attribution survives to the emissions record. Insert-time only and never a
    #: content-hash input: ``None`` stays NULL, so an unresolved supplier is
    #: never invented and existing snapshot hashes are unchanged.
    supplier_id: Optional[str] = None
    factor: Optional[EmissionFactor] = None
    customer_factor: Optional[CustomerFactor] = None

    @property
    def factor_kind(self) -> str:
        """Snapshot provenance discriminator (O1)."""
        return "customer_factor" if self.customer_factor is not None else "emission_factor"

    @property
    def customer_factor_id(self) -> Optional[str]:
        """The customer factor id when a customer factor is used (O1)."""
        return self.customer_factor.id if self.customer_factor is not None else None

    def __post_init__(self) -> None:
        if not self.match_request_id:
            raise ValueError("match_request_id must not be empty")
        if not self.organization_id:
            raise ValueError("organization_id must not be empty")
        if self.factor is None and self.customer_factor is None:
            raise ValueError(
                "a calculation requires a matched factor or a customer factor"
            )
        if self.factor is not None and self.customer_factor is not None:
            raise ValueError(
                "a calculation cannot use both an emission factor and a customer factor"
            )
        if self.quantity < 0:
            raise ValueError("quantity must be >= 0")
        if not self.quantity_unit:
            raise ValueError("quantity_unit must not be empty")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
        if not self.activity:
            raise ValueError("activity must not be empty")
        if not self.activity_type:
            raise ValueError("activity_type must not be empty")
        # ------------------------------------------------------------------
        # P0-2 — canonical unit resolution at the deterministic engine boundary.
        # Every calculation path (automatic pipeline, operations, customer,
        # consultant, exports) funnels through CalculationRequest, so
        # normalising quantity_unit here guarantees unit aliases (m3 ↔ cubic
        # metres, L ↔ litres, kWh ↔ kWh (Gross CV)) never reach the mismatch
        # check unresolved, while genuinely incompatible units still fail
        # deterministically downstream (UNIT_MISMATCH). Snapshots and emission
        # logs therefore persist canonical units.
        # ------------------------------------------------------------------
        _factor_unit: Optional[str] = (
            self.factor.unit
            if self.factor is not None
            else (self.customer_factor.unit if self.customer_factor is not None else None)
        )
        if _factor_unit:
            _resolved = resolve_unit_for_factor(self.quantity_unit, _factor_unit)
            if _resolved != self.quantity_unit:
                object.__setattr__(self, "quantity_unit", _resolved)
        # ------------------------------------------------------------------
        # P0-3 — methodology normalisation at the engine boundary. Only
        # canonical CalculationMethodology values may reach persistence.
        # Internal implementation labels from factor matching
        # ("customer_factor", "keyword_search", matching stage names) are
        # derived into a canonical methodology; any other non-canonical value
        # fails safely (never silently accepted).
        # ------------------------------------------------------------------
        try:
            CalculationMethodology(self.methodology)
        except ValueError:
            _canonical = derive_methodology(
                self.methodology,
                is_customer_factor=self.customer_factor is not None,
                quantity_unit=self.quantity_unit,
            )
            if _canonical is None:
                raise ValidationFailedError(
                    f"unknown calculation methodology {self.methodology!r}",
                    details={"methodology": self.methodology},
                ) from None
            object.__setattr__(self, "methodology", _canonical)

    @classmethod
    def from_match_result(
        cls,
        match: MatchResult,
        *,
        organization_id: str,
        quantity: Decimal,
        quantity_unit: str,
        date: _Date,
        reporting_year: int,
        activity: str,
        activity_type: str,
        scope: Optional[str] = None,
        methodology: str = CalculationMethodology.DIRECT_MULTIPLY.value,
        source_file: Optional[str] = None,
        source_page: Optional[int] = None,
        log_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        facility_id: Optional[str] = None,
        customer_factor: Optional[CustomerFactor] = None,
        performed_by: Optional[str] = None,
        accounting_dimensions: Optional[AccountingDimensions] = None,
        source_item_id: Optional[str] = None,
        source_line_item_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
    ) -> CalculationRequest:
        """Build a calculation request from the Phase 4 matching output.

        ``supplier_id`` (P17-IMPLEMENT-09) carries the already-authorized
        supplier attribution through to ``emissions_logs.supplier_id``. It is an
        insert-time only value and is deliberately NOT part of the content hash
        or the request-id derivation, so the attribution reaches the operational
        record without changing any existing snapshot's hash or identity.

        ``customer_factor`` must be supplied when ``match`` resolved to an
        approved customer factor (D-cf-5). A CarbonTally-managed match requires
        ``match.factor``.

        Raises:
            ValidationFailedError: When ``match`` did not resolve to a factor.
        """
        if match.status != "matched":
            raise ValidationFailedError(
                "calculation requires a matched factor from the matching engine",
                details={"status": match.status},
            )
        if match.factor_kind == "customer_factor":
            if customer_factor is None:
                raise ValidationFailedError(
                    "a customer-factor match requires the customer factor object",
                    details={"customer_factor_id": match.customer_factor_id},
                )
            if match.customer_factor_id and customer_factor.id != match.customer_factor_id:
                raise ValidationFailedError(
                    "customer factor id does not match the match result",
                    details={
                        "match_id": match.customer_factor_id,
                        "supplied_id": customer_factor.id,
                    },
                )
            factor = None
        else:
            if match.factor is None:
                raise ValidationFailedError(
                    "calculation requires a matched factor from the matching engine",
                    details={"status": match.status},
                )
            factor = match.factor
        return cls(
            match_request_id=match.request_id,
            organization_id=organization_id,
            factor=factor,
            quantity=quantity,
            quantity_unit=quantity_unit,
            date=date,
            reporting_year=reporting_year,
            activity=activity,
            activity_type=activity_type,
            scope=scope,
            methodology=methodology,
            source_file=source_file,
            source_page=source_page,
            log_id=log_id,
            asset_id=asset_id,
            facility_id=facility_id,
            customer_factor=customer_factor,
            performed_by=performed_by,
            accounting_dimensions=accounting_dimensions,
            source_item_id=source_item_id,
            source_line_item_id=source_line_item_id,
            supplier_id=supplier_id,
        )


class CalculationEngine:
    """Reproducible CO2e calculation pipeline with immutable snapshots.

    Args:
        sink: The repository surface used for snapshot and emissions-log
            persistence (:class:`CalculationSink`).
        event_bus: Optional bus that receives ``CalculationRequested`` and
            ``CalculationCompleted`` events (fire-and-forget).
        audit_logger: Optional logger that records every calculation outcome.
        algorithm_version: Version stamped into every snapshot (configuration;
            defaults to :data:`DEFAULT_ALGORITHM_VERSION`).
    """

    def __init__(
        self,
        sink: CalculationSink,
        *,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
        algorithm_version: str = DEFAULT_ALGORITHM_VERSION,
    ) -> None:
        if sink is None:
            raise ValueError("sink must not be None")
        if not algorithm_version:
            raise ValueError("algorithm_version must not be empty")
        self._sink = sink
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._algorithm_version = algorithm_version

    @property
    def algorithm_version(self) -> str:
        """The algorithm version stamped into generated snapshots."""
        return self._algorithm_version

    async def calculate(self, request: CalculationRequest) -> CalculationResult:
        """Run the calculation pipeline and persist the snapshot + log.

        Pipeline: publish ``CalculationRequested`` → apply the factor
        (unit validation + ``RESULT_PRECISION`` quantisation) → build the
        snapshot with content hash → persist snapshot → persist/update the
        emissions log → publish ``CalculationCompleted`` → audit → return the
        :class:`CalculationResult`.

        Raises:
            UnitMismatchError: When ``request.quantity_unit`` does not match
                the factor's unit (from
                :meth:`EmissionFactor.calculate_emissions`).
        """
        # P17-IMPLEMENT-04 — validate the accounting identity BEFORE any side
        # effect: before the ``CalculationRequested`` event, before the snapshot
        # INSERT and before the emissions log. A refused calculation therefore
        # leaves nothing behind, which is the only way to guarantee a refused
        # accounting result cannot become a partially written one.
        #
        # This mirrors the P17-A database constraints (NOT VALID, so historical
        # rows are exempt while every new write is enforced). Refusing here turns
        # what the database would reject anyway into a clean domain error instead
        # of a raw constraint violation surfacing to the user (AGENTS.md §46).
        validate_scope_dimensions(request.scope, request.accounting_dimensions)
        await self._publish_requested(request)
        co2e_kg = self._compute_co2e(request)
        snapshot = self._build_snapshot(request, co2e_kg)
        stored_snapshot = await self._sink.save_snapshot(
            snapshot,
            activity=request.activity,
            activity_type=request.activity_type,
            factor_source=(
                request.customer_factor.factor_source
                if request.customer_factor is not None
                else request.factor.factor_source or None
            ),
            factor_set="CUSTOMER" if request.customer_factor is not None else request.factor.factor_set or None,
            import_batch_id=None if request.customer_factor is not None else request.factor.import_batch_id,
            calculated_by=request.organization_id,
            # Gate-4 remediation F1 — the actual human/entity actor (when the
            # calculation was performed by a human through the ops/PE surfaces)
            # is persisted on the snapshot instead of relying on the
            # organisation id alone.
            performed_by=request.performed_by,
            factor_kind=request.factor_kind,
            customer_factor_id=request.customer_factor_id,
        )
        await self._persist_log(request, stored_snapshot, co2e_kg)
        verification = self.verify(stored_snapshot)
        if not verification.match:
            logger.warning(
                "calculation verification failed for snapshot %s "
                "(discrepancy %s)",
                stored_snapshot.id,
                verification.discrepancy,
            )
        await self._publish_completed(stored_snapshot)
        await self._audit(request, stored_snapshot, co2e_kg)
        return CalculationResult(
            co2e_kg=co2e_kg,
            co2e_tonnes=(co2e_kg / Decimal("1000")).quantize(_TONNES_PRECISION),
            snapshot=stored_snapshot,
            factor_used=request.factor,
            methodology=CalculationMethodology(request.methodology),
            customer_factor=request.customer_factor,
        )

    def _compute_co2e(self, request: CalculationRequest) -> Decimal:
        """Apply the active factor (CarbonTally or customer-owned) exactly.

        The customer-factor path applies ``quantity * co2e_multiplier`` with the
        same ``RESULT_PRECISION`` quantisation as
        :meth:`EmissionFactor.calculate_emissions`, preserving reproducibility.
        """
        if request.customer_factor is not None:
            customer = request.customer_factor
            if customer.unit is not None and request.quantity_unit != customer.unit:
                raise UnitMismatchError(
                    f"consumption unit {request.quantity_unit!r} does not match "
                    f"customer factor unit {customer.unit!r} for factor {customer.id}"
                )
            return (request.quantity * customer.co2e_multiplier).quantize(
                RESULT_PRECISION
            )
        return request.factor.calculate_emissions(
            request.quantity, request.quantity_unit
        )

    def verify(self, snapshot: CalculationSnapshot) -> VerificationResult:
        """Recompute the snapshot and check reproducibility + tamper evidence.

        ``match`` compares the recomputed ``co2e_kg`` with the stored value;
        ``tampered`` is ``True`` when the stored ``content_hash`` does not match
        a freshly computed hash of the snapshot's inputs.
        """
        recomputed = (snapshot.quantity * snapshot.co2e_multiplier).quantize(
            RESULT_PRECISION
        )
        match = snapshot.verify_reproducibility(recomputed)
        tampered = (
            bool(snapshot.content_hash)
            and snapshot.content_hash != snapshot.build_content_hash()
        )
        discrepancy = None if match else recomputed - snapshot.co2e_kg
        return VerificationResult(
            match=match, discrepancy=discrepancy, tampered=tampered
        )

    def _build_snapshot(
        self, request: CalculationRequest, co2e_kg: Decimal
    ) -> CalculationSnapshot:
        if request.customer_factor is not None:
            multiplier = request.customer_factor.co2e_multiplier
            factor_id: Optional[str] = None
        else:
            multiplier = request.factor.co2e_multiplier
            factor_id = request.factor.id
        snapshot = CalculationSnapshot(
            id=str(uuid.uuid4()),
            match_request_id=request.match_request_id,
            organization_id=request.organization_id,
            factor_id=factor_id,
            quantity=request.quantity,
            quantity_unit=request.quantity_unit,
            co2e_multiplier=multiplier,
            co2e_kg=co2e_kg,
            scope=request.scope,
            date=request.date,
            reporting_year=request.reporting_year,
            methodology=request.methodology,
            algorithm_version=self._algorithm_version,
            created_at=_Date.today(),
            content_hash="",
            factor_kind=request.factor_kind,
            customer_factor_id=request.customer_factor_id,
            source_file=request.source_file,
            source_page=request.source_page,
            source_item_id=request.source_item_id,
            source_line_item_id=request.source_line_item_id,
            # P17-IMPLEMENT-04 — the canonical accounting dimensions travel with
            # the snapshot. They are excluded from content_hash (see
            # CalculationSnapshot._canonical), so P16 snapshot identity and
            # idempotency are unchanged.
            accounting_dimensions=request.accounting_dimensions,
        )
        return dataclasses.replace(
            snapshot, content_hash=snapshot.build_content_hash()
        )

    async def _persist_log(
        self,
        request: CalculationRequest,
        snapshot: CalculationSnapshot,
        co2e_kg: Decimal,
    ) -> EmissionLog:
        """Write the calculated figure + snapshot link to the emissions log.

        The customer-factor path (O1) stores a NULL ``emission_factor_id`` — the
        column is nullable in the RC2 schema and the customer factor is not an
        ``emission_factors`` row (its provenance lives on the snapshot).
        """
        log_factor_id = (
            None if request.customer_factor is not None else request.factor.id
        )
        if request.log_id is not None:
            log = EmissionLog(
                id=request.log_id,
                organization_id=request.organization_id,
                factor_id=log_factor_id,  # type: ignore[arg-type]
                quantity=request.quantity,
                date=request.date,
                unit=request.quantity_unit,
                scope=request.scope,
                asset_id=request.asset_id,
                facility_id=request.facility_id,
                snapshot_id=snapshot.id,
                calculated_kg_co2e=co2e_kg,
                accounting_dimensions=request.accounting_dimensions,
            )
            self._assert_log_matches_snapshot(snapshot, log)
            return await self._sink.save(log)
        created = await self._sink.create(
            org_id=request.organization_id,
            factor_id=log_factor_id,
            quantity=request.quantity,
            unit=request.quantity_unit,
            scope=request.scope,
            date=request.date,
            asset_id=request.asset_id,
            facility_id=request.facility_id,
            snapshot_id=snapshot.id,
            supplier_id=request.supplier_id,
            # P17-IMPLEMENT-09 — the dimensions must be present on the INSERT, not
            # only on the later UPDATE: the P17-A CHECK constraints on
            # ``emissions_logs`` are NOT VALID for historical rows but enforced on
            # every NEW row, so a Scope 2/3 log inserted without its method or
            # category is rejected by PostgreSQL before the update can run.
            accounting_dimensions=request.accounting_dimensions,
        )
        updated = dataclasses.replace(
            created,
            calculated_kg_co2e=co2e_kg,
            snapshot_id=snapshot.id,
            # P17-IMPLEMENT-04 — the SAME dimensions object as the snapshot, so
            # the pair cannot disagree about owner, acting-for or accounting
            # identity. Both are derived from one ``request``, so consistency is
            # structural rather than a convention.
            accounting_dimensions=request.accounting_dimensions,
        )
        self._assert_log_matches_snapshot(snapshot, updated)
        return await self._sink.save(updated)

    @staticmethod
    def _assert_log_matches_snapshot(
        snapshot: CalculationSnapshot, log: EmissionLog
    ) -> None:
        """Refuse an emissions log whose ownership disagrees with its snapshot.

        Phase 4 / Phase 11 of P17-IMPLEMENT-04: an emissions log must always
        correspond to the authoritative calculation snapshot. The engine derives
        both from one ``CalculationRequest``, so a mismatch indicates a
        programming error rather than user input — which is exactly why it is a
        hard failure instead of a warning. Failing here is safe: nothing has been
        written for this log yet, and the snapshot remains the authoritative
        record the caller can retry against.

        ``acting_for_organization_id`` is compared only when both sides carry it,
        so a Scope 1 P16-era calculation with no dimensions is unaffected.
        """
        if log.organization_id != snapshot.organization_id:
            raise ValueError(
                "emissions log organization "
                f"{log.organization_id!r} does not match snapshot organization "
                f"{snapshot.organization_id!r}; refusing to attribute a log to a "
                "different data owner than its authoritative snapshot"
            )
        log_dims = log.accounting_dimensions
        snapshot_dims = snapshot.accounting_dimensions
        if log_dims is None or snapshot_dims is None:
            return
        if (
            log_dims.acting_for_organization_id
            != snapshot_dims.acting_for_organization_id
        ):
            raise ValueError(
                "emissions log acting_for_organization_id "
                f"{log_dims.acting_for_organization_id!r} does not match snapshot "
                f"acting_for_organization_id "
                f"{snapshot_dims.acting_for_organization_id!r}; refusing to write "
                "an inconsistently attributed accounting result"
            )

    async def _publish_requested(self, request: CalculationRequest) -> None:
        if self._event_bus is None:
            return
        event = CalculationRequested(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            correlation_id=request.match_request_id,
            match_request_id=request.match_request_id,
            organization_id=request.organization_id,
        )
        await self._publish(event, request.match_request_id)

    async def _publish_completed(self, snapshot: CalculationSnapshot) -> None:
        if self._event_bus is None:
            return
        event = CalculationCompleted(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            correlation_id=snapshot.match_request_id,
            snapshot_id=snapshot.id,
            co2e_kg=snapshot.co2e_kg,
        )
        await self._publish(event, snapshot.match_request_id)

    async def _publish(self, event: DomainEvent, correlation_id: str) -> None:
        if self._event_bus is None:
            return
        try:
            await self._event_bus.publish(event)
        except Exception:  # noqa: BLE001 - side effects must not break the calculation
            logger.exception(
                "failed to publish %s for correlation %s",
                type(event).__name__,
                correlation_id,
            )

    async def _audit(
        self,
        request: CalculationRequest,
        snapshot: CalculationSnapshot,
        co2e_kg: Decimal,
    ) -> None:
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="calculation:completed",
                entity_type="calculation_snapshot",
                entity_id=snapshot.id,
                correlation_id=request.match_request_id,
                # Gate-4 remediation F1 — prefer the actual human actor when a
                # calculation was requested by a human; fall back to the engine
                # label for automatic runs.
                actor=request.performed_by or "calculation_engine",
                after={
                    "co2e_kg": str(co2e_kg),
                    "methodology": snapshot.methodology,
                    "algorithm_version": snapshot.algorithm_version,
                    "factor_id": snapshot.factor_id,
                    "factor_kind": snapshot.factor_kind,
                    "customer_factor_id": snapshot.customer_factor_id,
                    "content_hash": snapshot.content_hash,
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break the calculation
            logger.exception(
                "failed to audit calculation for snapshot %s", snapshot.id
            )



