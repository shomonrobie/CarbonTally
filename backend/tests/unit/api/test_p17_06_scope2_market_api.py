"""P17-IMPLEMENT-06 — MARKET_BASED Scope 2 through the real HTTP route.

Exercises ``POST /api/v3/scope2/calculate`` end to end: server-side accounting
context, server-side instrument load, the existing Scope 2 service, the canonical
``CalculationEngine`` write and idempotent allocation persistence.

Only the database is faked (repositories + the authorization dependency); the
route, the service, the engine and the domain rules are the real ones.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

import api.v3_scope2 as scope2_api
from api.accounting_context_auth import AccountingContext
from api.dependencies import get_repositories
from api.v3_scope2 import router as scope2_router
from auth import AuthUser, get_current_user
from core.exceptions import ActingForError, CarbonTallyError
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.accounting_dimensions import AccountingDimensions
from domain.contractual_instruments import INSTRUMENT_TYPES, ContractualInstrument
from domain.factor import EmissionFactor

OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
OTHER = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
USER_ID = "66666666-6666-4666-8666-666666666666"
FACTOR_ID = "f-11111111"
INSTRUMENT_ID = "11111111-1111-4111-8111-111111111111"
_ACTIVITY = "Electricity > Grid > UK grid electricity (kg CO2e) [kWh]"


class _RecordingSink:
    """In-memory ``CalculationSink`` (the engine's persistence surface)."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
        self.saved: list[EmissionLog] = []

    async def save_snapshot(self, snapshot: CalculationSnapshot, **kwargs: Any):
        self.snapshots.append(snapshot)
        return snapshot

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: Any,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
        supplier_id: Optional[str] = None,
        accounting_dimensions: Optional[AccountingDimensions] = None,
    ) -> EmissionLog:
        return EmissionLog(
            id="99999999-9999-4999-8999-999999999999",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
        )

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.saved.append(entity)
        return entity


class _FactorRepo:
    def __init__(self, factor: Optional[EmissionFactor]) -> None:
        self._factor = factor

    async def get(self, id: str) -> Optional[EmissionFactor]:
        return self._factor if self._factor and self._factor.id == id else None


def make_factor(**over: Any) -> EmissionFactor:
    return EmissionFactor(
        id=over.get("id", FACTOR_ID),
        reporting_year=int(over.get("year", 2025)),
        activity_type=_ACTIVITY,
        co2e_multiplier=Decimal(str(over.get("multiplier", "0.20700"))),
        unit="kWh",
        scope=str(over.get("scope", "Scope 2")),
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country=str(over.get("country", "GB")),
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ACTIVITY, "GB", "kWh", "Scope 2"),
    )


def make_instrument(**over: Any) -> ContractualInstrument:
    return ContractualInstrument(
        id=over.get("id", INSTRUMENT_ID),
        organization_id=str(over.get("organization_id", OWNER)),
        instrument_type=str(over.get("instrument_type", INSTRUMENT_TYPES[0])),
        identifier=str(over.get("identifier", "GO-2025-0001")),
        geography=str(over.get("geography", "GB")),
        quantity=Decimal(str(over.get("quantity", "1000"))),
        unit=str(over.get("unit", "kWh")),
        vintage_year=over.get("vintage_year", 2025),
        retirement_status=str(over.get("retirement_status", "active")),
    )


class _InstrumentRepo:
    """Stands in for the trusted repository: tenant-scoped, fail-closed.

    ``get_for_organization`` mirrors the real SQL predicate — it returns ``None``
    unless the instrument's owner matches the requested organization, so the fake
    cannot accidentally be more permissive than the repository it replaces.
    """

    def __init__(
        self,
        instrument: Optional[ContractualInstrument] = None,
        allocations: Optional[list[Any]] = None,
    ) -> None:
        self._instrument = instrument
        self._allocations = allocations or []
        self.recorded: list[Any] = []
        self.record_calls = 0
        self.existing_for_request: Optional[str] = None
        self.load_scopes: list[tuple[str, str]] = []

    async def get_for_organization(
        self, instrument_id: str, organization_id: str
    ) -> Optional[ContractualInstrument]:
        self.load_scopes.append((instrument_id, organization_id))
        if self._instrument is None:
            return None
        if self._instrument.id != instrument_id:
            return None
        if self._instrument.organization_id != organization_id:
            return None
        return self._instrument

    async def list_allocations(self, instrument_id: str, organization_id: str):
        return list(self._allocations)

    async def find_allocation_for_request(self, **kwargs: Any) -> Optional[str]:
        return self.existing_for_request

    async def record_allocation(self, allocation: Any) -> Optional[str]:
        self.record_calls += 1
        self.recorded.append(allocation)
        return "77777777-7777-4777-8777-777777777777"


class _Bundle:
    def __init__(
        self,
        factor: Optional[EmissionFactor],
        sink: _RecordingSink,
        instruments: Optional[_InstrumentRepo],
    ) -> None:
        self.factors = _FactorRepo(factor)
        self.logs = sink
        self.contractual_instruments = instruments


def _context(**over: Any) -> AccountingContext:
    base = dict(
        actor_user_id=USER_ID,
        persona="CONSULTANT",
        own_organization_id=FIRM,
        data_owning_organization_id=OWNER,
        acting_for_organization_id=OWNER,
        acting_for_organization_name="Client Co",
        actor_organization_id=FIRM,
        is_delegated=True,
        entitlement_basis="CONSULTANT_CLIENT",
        acting_for_kind="CONSULTANT_TEAM_FOR_CLIENT",
    )
    base.update(over)
    return AccountingContext(**base)


def _user() -> AuthUser:
    """An organisation member of the data-owning organization.

    The route's pre-existing ``require_org_member()`` gate is unchanged and must
    be satisfied; the consultant/delegated case is exercised through the resolved
    accounting context (patched below), which is what actually decides the
    authorization and attribution.
    """
    return AuthUser(
        user_id=USER_ID,
        email="c@example.com",
        role="org_owner",
        role_name="owner",
        organization_id=OWNER,
        is_org_member=True,
        is_admin=True,
    )


def _app(bundle: _Bundle, *, context: Any = None) -> FastAPI:
    app = FastAPI()
    app.include_router(scope2_router)

    @app.exception_handler(CarbonTallyError)
    async def _handler(request, exc: CarbonTallyError):  # noqa: ANN001
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    async def _ctx(current_user, repos, organization_id):  # noqa: ANN001
        if isinstance(context, Exception):
            raise context
        return context if context is not None else _context()

    app.dependency_overrides[get_current_user] = lambda: _user()
    app.dependency_overrides[get_repositories] = lambda: bundle
    scope2_api.ensure_record_owner_authorized = _ctx  # type: ignore[assignment]
    return app


def _payload(**over: Any) -> dict:
    base = {
        "organization_id": OWNER,
        "scope2_method": "LOCATION_BASED",
        "energy_type": "electricity",
        "quantity": "100",
        "unit": "kWh",
        "date": "2025-06-01",
        "reporting_year": 2025,
        "activity": "Grid electricity",
        "activity_type": _ACTIVITY,
        "factor_id": FACTOR_ID,
    }
    base.update(over)
    return base


def _market(*, instruments: _InstrumentRepo, **over: Any) -> dict:
    return _payload(scope2_method="MARKET_BASED", instrument_id=INSTRUMENT_ID, **over)


# ===========================================================================
# 1. LOCATION_BASED regression — unchanged behaviour
# ===========================================================================
def test_location_based_request_still_works_and_reports_no_instrument() -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _InstrumentRepo())))
    response = client.post("/api/v3/scope2/calculate", json=_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope2_method"] == "LOCATION_BASED"
    assert body["co2e_kg"] == "20.700000"
    # No instrument, no allocation — that is what distinguishes the methods.
    assert body["instrument_id"] is None
    assert body["allocation_id"] is None
    assert len(sink.snapshots) == 1


# ===========================================================================
# 2 / 3. MARKET_BASED success with a repository-backed instrument
# ===========================================================================
def test_market_based_with_a_tenant_owned_instrument_succeeds() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(organization_id=OWNER))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope2_method"] == "MARKET_BASED"
    assert body["energy_type"] == "electricity"
    assert body["co2e_kg"] == "20.700000"
    # Market-based provenance is returned, not inferred.
    assert body["instrument_id"] == INSTRUMENT_ID
    assert body["allocation_id"] == "77777777-7777-4777-8777-777777777777"
    # The instrument was loaded scoped to the RESOLVED data owner.
    assert repo.load_scopes == [(INSTRUMENT_ID, OWNER)]
    # The claim was recorded once, after the calculation succeeded.
    assert repo.record_calls == 1
    assert repo.recorded[0].calculation_snapshot_id == sink.snapshots[0].id
    assert repo.recorded[0].organization_id == OWNER


def test_allocation_is_written_only_after_the_snapshot_exists() -> None:
    """Failure cannot create an allocation the calculation did not persist."""
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    snapshot_id = sink.snapshots[0].id
    assert repo.recorded[0].calculation_snapshot_id == snapshot_id
    assert snapshot_id, "the allocation references a real persisted snapshot"


# ===========================================================================
# 4. Cross-tenant instrument
# ===========================================================================
def test_cross_tenant_instrument_is_rejected_and_reveals_nothing() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(organization_id=OTHER))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INSTRUMENT_NOT_ELIGIBLE"
    # Nothing was calculated and no allocation was written.
    assert sink.snapshots == []
    assert repo.record_calls == 0
    # The load was still scoped to the authorized owner, not to the payload.
    assert repo.load_scopes == [(INSTRUMENT_ID, OWNER)]


# ===========================================================================
# 5. Unauthorized acting-for
# ===========================================================================
def test_unauthorized_acting_for_context_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    app = _app(_Bundle(make_factor(), sink, repo), context=ActingForError("denied"))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 403
    assert sink.snapshots == []
    assert repo.load_scopes == []


# ===========================================================================
# 6 / 7 / 8 / 9. Instrument eligibility failures
# ===========================================================================
def test_missing_instrument_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(None)
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 422
    assert sink.snapshots == []


def test_inactive_instrument_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(retirement_status="retired"))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 422
    assert sink.snapshots == []


def test_wrong_geography_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(geography="FR"))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post(
        "/api/v3/scope2/calculate", json=_market(instruments=repo, geography="GB")
    )
    assert response.status_code == 422
    assert sink.snapshots == []


def test_wrong_vintage_year_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(vintage_year=2023))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 422
    assert sink.snapshots == []


# ===========================================================================
# 10 / 14 / 15. Method + energy type, and never downgrading
# ===========================================================================
def test_market_based_without_an_instrument_id_is_rejected_not_downgraded() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post(
        "/api/v3/scope2/calculate", json=_payload(scope2_method="MARKET_BASED")
    )
    assert response.status_code == 422
    message = response.json()["error"]["message"]
    assert "never substituted automatically" in message
    assert sink.snapshots == []
    assert repo.record_calls == 0


def test_invalid_energy_type_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post(
        "/api/v3/scope2/calculate", json=_market(instruments=repo, energy_type="biomass")
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ACCOUNTING_DIMENSION_INVALID"
    assert sink.snapshots == []



# ===========================================================================
# 11 / 12 / 13. Allocation sufficiency, DC-09, unit coherence
# ===========================================================================
def test_insufficient_allocation_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post(
        "/api/v3/scope2/calculate",
        json=_market(instruments=repo, allocated_quantity="10"),
    )
    assert response.status_code == 422
    assert sink.snapshots == []


def test_dc09_over_allocation_is_rejected() -> None:
    from datetime import date as _date

    from domain.contractual_instruments import InstrumentAllocation

    sink = _RecordingSink()
    existing = [
        InstrumentAllocation(
            organization_id=OWNER,
            instrument_id=INSTRUMENT_ID,
            allocated_quantity=Decimal("950"),
            allocated_unit="kWh",
            allocation_period_start=_date(2025, 1, 1),
            allocation_period_end=_date(2025, 12, 31),
        )
    ]
    repo = _InstrumentRepo(make_instrument(quantity="1000"), existing)
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSTRUMENT_OVER_ALLOCATED"
    assert sink.snapshots == []
    assert repo.record_calls == 0


def test_unit_mismatch_is_rejected() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(unit="kWh"))
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post(
        "/api/v3/scope2/calculate", json=_market(instruments=repo, unit="MWh")
    )
    assert response.status_code == 422
    assert sink.snapshots == []


# ===========================================================================
# 16 / 17. Idempotency and attribution separation
# ===========================================================================
def test_repeated_identical_request_does_not_record_a_second_allocation() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    repo.existing_for_request = "88888888-8888-4888-8888-888888888888"
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 200
    # The claim already existed, so nothing new was written.
    assert repo.record_calls == 0
    assert response.json()["allocation_id"] == "88888888-8888-4888-8888-888888888888"


def test_owner_and_acting_for_remain_distinct() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    body = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo)).json()
    assert body["organization_id"] == OWNER
    assert body["acting_for_organization_id"] == OWNER
    assert body["performed_by_organization_id"] == FIRM
    # The owner is the data owner, never the actor's own (firm) organization.
    assert body["organization_id"] != body["performed_by_organization_id"]
    assert repo.recorded[0].organization_id == OWNER


def test_repeated_identically_derived_requests_share_the_request_identity() -> None:
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument())
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    first = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo)).json()
    second = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo)).json()
    assert first["request_id"] == second["request_id"]
    assert first["content_hash"] == second["content_hash"]


def test_a_cross_tenant_actor_cannot_borrow_another_tenants_instrument() -> None:
    """The payload names the owner; the instrument still must belong to it."""
    sink = _RecordingSink()
    repo = _InstrumentRepo(make_instrument(organization_id=OWNER))
    # The context resolves to a DIFFERENT data owner than the instrument's.
    app = _app(
        _Bundle(make_factor(), sink, repo),
        context=_context(data_owning_organization_id=OTHER),
    )
    client = TestClient(app)
    response = client.post("/api/v3/scope2/calculate", json=_market(instruments=repo))
    assert response.status_code == 422
    assert repo.load_scopes == [(INSTRUMENT_ID, OTHER)]
    assert sink.snapshots == []
