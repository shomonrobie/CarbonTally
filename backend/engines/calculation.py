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
    methodology: str = CalculationMethodology.DIRECT_MULTIPLY.value
    source_file: Optional[str] = None
    source_page: Optional[int] = None
    log_id: Optional[str] = None
    asset_id: Optional[str] = None
    facility_id: Optional[str] = None
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
        try:
            CalculationMethodology(self.methodology)
        except ValueError as exc:
            raise ValidationFailedError(
                f"unknown calculation methodology {self.methodology!r}",
                details={"methodology": self.methodology},
            ) from exc

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
    ) -> CalculationRequest:
        """Build a calculation request from the Phase 4 matching output.

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
            )
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
        )
        updated = dataclasses.replace(
            created, calculated_kg_co2e=co2e_kg, snapshot_id=snapshot.id
        )
        return await self._sink.save(updated)

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
                actor="calculation_engine",
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



