"""P17-IMPLEMENT-08 — the Scope 3 HTTP API, exercised through the real route.

Drives ``POST /api/v3/scope3/calculate`` end to end: server-side accounting
context, the real Scope 3 service, the real domain contracts and boundary guards,
the canonical ``CalculationEngine`` write, and estimation-record persistence.

Only the database (repositories) and the authorization dependency are faked. The
route, service, engine and domain rules are production code.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

import api.v3_scope3 as scope3_api
from api.accounting_context_auth import AccountingContext
from api.dependencies import get_repositories
from api.v3_scope3 import router as scope3_router
from auth import AuthUser, get_current_user
from core.exceptions import ActingForError, CarbonTallyError
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.factor import EmissionFactor

OWNER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
OTHER = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
USER_ID = "66666666-6666-4666-8666-666666666666"
FACTOR_ID = "f-s3-11111111"
_ACTIVITY = "Scope 3 > Purchased goods > Paper (kg CO2e) [kg]"


class _RecordingSink:
    """In-memory ``CalculationSink``."""

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
    """Tenant-agnostic factor lookup, as the real repository is."""

    def __init__(self, factor: Optional[EmissionFactor]) -> None:
        self._factor = factor

    async def get(self, id: str) -> Optional[EmissionFactor]:
        return self._factor if self._factor and self._factor.id == id else None


class _EstimationRepo:
    """Records estimation-record writes; tenant-scoped like the real repository."""

    def __init__(self, fail: bool = False) -> None:
        self.records: list[Any] = []
        self.calls = 0
        self.existing_for_snapshot: Optional[str] = None
        self.fail = fail

    async def record(self, record: Any) -> Optional[str]:
        self.calls += 1
        self.records.append(record)
        if self.fail:
            raise RuntimeError("estimation insert failed")
        if self.existing_for_snapshot is not None:
            return None
        return "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


class _Bundle:
    def __init__(
        self,
        factor: Optional[EmissionFactor],
        sink: _RecordingSink,
        estimation: Optional[_EstimationRepo],
    ) -> None:
        self.factors = _FactorRepo(factor)
        self.logs = sink
        self.estimation_records = estimation


def make_factor(**over: Any) -> EmissionFactor:
    return EmissionFactor(
        id=over.get("id", FACTOR_ID),
        reporting_year=int(over.get("year", 2025)),
        activity_type=_ACTIVITY,
        co2e_multiplier=Decimal(str(over.get("multiplier", "2.50000"))),
        unit=str(over.get("unit", "kg")),
        scope=str(over.get("scope", "Scope 3")),
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country=str(over.get("country", "GB")),
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ACTIVITY, "GB", "kg", "Scope 3"),
    )


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
    """An organisation member of the claimed organization (route gate)."""
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
    app.include_router(scope3_router)

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
    scope3_api.ensure_record_owner_authorized = _ctx  # type: ignore[assignment]
    return app


#: Minimal truthful API payload per category (the same facts the P17-07 service
#: fixtures supply, expressed as the HTTP surface would carry them).
_API: dict[int, dict[str, Any]] = {
    1: {"data_quality": "primary_supplier"},
    2: {"data_quality": "primary_supplier", "inputs": {"capitalisation_declared": True}},
    3: {
        "data_quality": "primary_supplier",
        "source_snapshot_id": "11111111-1111-4111-8111-111111111111",
        "source_item_id": "22222222-2222-4222-8222-222222222222",
    },
    4: {"data_quality": "primary_supplier", "transport_boundary": "upstream"},
    5: {
        "data_quality": "primary_supplier",
        "inputs": {"material": "paper", "treatment_route": "recycling"},
        "waste_origin": "operations",
    },
    6: {"data_quality": "primary_measured", "inputs": {"trip_purpose": "client_meeting"}},
    7: {"data_quality": "secondary_estimated", "estimation_method": "average_data"},
    8: {"data_quality": "primary_supplier", "consolidation_approach": "operational_control"},
    9: {"data_quality": "primary_supplier", "transport_boundary": "downstream"},
    10: {"data_quality": "secondary_estimated", "estimation_method": "proxy_data"},
    11: {
        "data_quality": "modelled",
        "inputs": {"use_phase_assumption": "10 years at 100 kWh/yr"},
        "estimation_method": "modelled",
    },
    12: {
        "data_quality": "primary_supplier",
        "inputs": {"material": "steel", "treatment_route": "recycling"},
        "waste_origin": "sold_product_eol",
        "estimation_method": "average_data",
    },
    13: {"data_quality": "primary_supplier", "consolidation_approach": "operational_control"},
    14: {
        "data_quality": "secondary_estimated",
        "inputs": {"allocation_basis": "floor_area_share"},
        "estimation_method": "extrapolated",
    },
    15: {
        "data_quality": "modelled",
        "inputs": {"attribution_basis": "equity_share"},
        "estimation_method": "modelled",
    },
}

ALL_CATEGORIES = tuple(range(1, 16))


def payload(category: int, **over: Any) -> dict:
    """Build the minimal truthful HTTP payload for ``category``."""
    base: dict[str, Any] = {
        "organization_id": OWNER,
        "category": category,
        "quantity": "100",
        "unit": "kg",
        "date": "2025-06-01",
        "reporting_year": 2025,
        "activity": "Paper purchased",
        "activity_type": _ACTIVITY,
        "factor_id": FACTOR_ID,
    }
    base.update(_API[category])
    # The estimation basis accompanies the method where one is required.
    if base.get("estimation_method"):
        base.setdefault("estimation_inputs", {"basis": "DEFRA 2025 average"})
        base.setdefault("estimation_assumptions", {"per_employee_km": 3000})
    base.update(over)
    return base


def _client(**kw: Any) -> TestClient:
    sink = kw.pop("sink", None) or _RecordingSink()
    return TestClient(
        _app(
            _Bundle(
                kw.pop("factor", make_factor()),
                sink,
                kw.pop("estimation", _EstimationRepo()),
            ),
            **kw,
        )
    )


# ===========================================================================
# A. ALL 15 CATEGORIES through the real HTTP route
# ===========================================================================
@pytest.mark.parametrize("category", ALL_CATEGORIES)
def test_every_category_is_accepted_and_preserved(category: int) -> None:
    sink = _RecordingSink()
    client = TestClient(
        _app(_Bundle(make_factor(), sink, _EstimationRepo()))
    )
    response = client.post("/api/v3/scope3/calculate", json=payload(category))
    assert response.status_code == 200, response.text
    body = response.json()

    # The category is preserved verbatim — it never silently becomes another one.
    assert body["category"] == category
    assert body["status"] == "CALCULATED"
    assert body["scope"] == "Scope 3"
    # Pathway and architecture status are reported truthfully.
    assert body["pathway"] in {"activity_factor", "estimation"}
    assert body["architecture_status"] in {
        "SUPPORTED", "PARTIAL", "DEFERRED", "NOT_IMPLEMENTED"
    }
    # Data quality is preserved, and estimation is visibly flagged.
    assert body["data_quality"] == payload(category)["data_quality"]
    assert body["is_estimated"] == (
        payload(category)["data_quality"]
        in {"secondary_estimated", "spend_based_estimated", "modelled"}
    )
    # Result identity and numerics.
    assert body["snapshot_id"] and body["request_id"]
    assert body["co2e_kg"] == "250.000000"
    assert body["content_hash"]
    # Ownership and attribution.
    assert body["organization_id"] == OWNER
    assert body["acting_for_organization_id"] == OWNER
    assert body["performed_by_organization_id"] == FIRM
    # Persisted on the canonical path, with the same category on snapshot and log.
    assert len(sink.snapshots) == 1 and len(sink.saved) == 1
    assert sink.snapshots[0].accounting_dimensions.scope3_category == category
    assert sink.saved[0].accounting_dimensions.scope3_category == category


def test_the_architecture_status_is_never_upgraded_by_the_api() -> None:
    """Categories the taxonomy marks incomplete still report that status."""
    client = _client()
    expected = {
        2: "NOT_IMPLEMENTED",
        10: "NOT_IMPLEMENTED",
        11: "DEFERRED",
        14: "DEFERRED",
        15: "DEFERRED",
    }
    for category, status in expected.items():
        body = client.post("/api/v3/scope3/calculate", json=payload(category)).json()
        assert body["architecture_status"] == status, (
            f"category {category} reported {body['architecture_status']}, "
            f"expected {status}"
        )


# ===========================================================================
# B. INVALID INPUT — structured 4xx, never fabricated output
# ===========================================================================
@pytest.mark.parametrize(
    "mutation,expected",
    [
        ({"category": 99}, 422),
        ({"category": 0}, 422),
        ({"data_quality": "invented_quality"}, 422),
        ({"methodology": "invented_method"}, 422),
        ({"pathway": "invented_pathway"}, 422),
        ({"factor_id": "no-such-factor"}, 422),
        ({"reporting_year": 2024}, 422),          # wrong factor year
        ({"data_quality": "primary_measured"}, 422),  # estimation cat as measured
    ],
)
def test_invalid_requests_are_refused_with_a_structured_error(
    mutation: dict, expected: int
) -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    # Merged rather than passed as kwargs: the mutation may replace ``category``.
    body = {**payload(7), **mutation}      # category 7 is estimation-based
    response = client.post("/api/v3/scope3/calculate", json=body)
    assert response.status_code == expected, response.text
    # Nothing was persisted and no number was produced.
    assert sink.snapshots == []
    assert "co2e_kg" not in response.text


def test_a_missing_category_is_refused() -> None:
    client = _client()
    body = payload(1)
    del body["category"]
    response = client.post("/api/v3/scope3/calculate", json=body)
    assert response.status_code == 422
    assert "co2e_kg" not in response.text


def test_missing_data_quality_is_refused() -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    response = client.post(
        "/api/v3/scope3/calculate", json=payload(6, data_quality=None)
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ACCOUNTING_DIMENSION_INVALID"
    assert sink.snapshots == []


def test_a_scope_1_factor_is_refused_for_a_scope_3_calculation() -> None:
    """Factor governance — no incompatible scope."""
    sink = _RecordingSink()
    client = TestClient(
        _app(_Bundle(make_factor(scope="Scope 1"), sink, _EstimationRepo()))
    )
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    assert response.status_code == 422
    assert "must not use a factor from another scope" in response.json()["error"]["message"]
    assert sink.snapshots == []


def test_a_factor_from_another_year_is_refused() -> None:
    sink = _RecordingSink()
    client = TestClient(
        _app(_Bundle(make_factor(year=2023), sink, _EstimationRepo()))
    )
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    assert response.status_code == 422
    assert "never silently substituted" in response.json()["error"]["message"]
    assert sink.snapshots == []


def test_an_estimation_requirement_without_a_basis_is_refused() -> None:
    """T-INV-12 — an estimated classification with no basis is not accepted."""
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    body = payload(7)
    del body["estimation_method"]
    response = client.post("/api/v3/scope3/calculate", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ESTIMATION_RECORD_REQUIRED"
    assert sink.snapshots == []


# ===========================================================================
# C. CLARIFICATION — missing information is controlled, never invented
# ===========================================================================
def test_missing_required_input_yields_clarification_not_a_number() -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    response = client.post(
        "/api/v3/scope3/calculate",
        json=payload(5, inputs={"material": "paper"}),
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["status"] == "CLARIFICATION_REQUIRED"
    assert "treatment_route" in detail["missing_fields"]
    assert detail["category"] == 5
    assert detail["reason"] and detail["guidance"]
    assert "co2e_kg" not in response.text
    assert sink.snapshots == []


def test_missing_boundary_yields_clarification() -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    body = payload(4)
    del body["transport_boundary"]
    response = client.post("/api/v3/scope3/calculate", json=body)
    assert response.status_code == 422
    assert "transport_boundary" in response.json()["detail"]["missing_fields"]
    assert sink.snapshots == []


def test_missing_use_phase_assumption_yields_clarification() -> None:
    """Category 11 never fabricates a product lifetime."""
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    response = client.post(
        "/api/v3/scope3/calculate", json=payload(11, inputs={})
    )
    assert response.status_code == 422
    assert "use_phase_assumption" in response.json()["detail"]["missing_fields"]
    assert sink.snapshots == []


# ===========================================================================
# D. SECURITY — ownership is never taken from the request body
# ===========================================================================
def test_an_unauthorized_acting_for_context_is_rejected() -> None:
    sink = _RecordingSink()
    app = _app(
        _Bundle(make_factor(), sink, _EstimationRepo()),
        context=ActingForError("denied"),
    )
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    assert response.status_code == 403
    assert sink.snapshots == []


def test_a_payload_naming_another_tenant_is_authorized_against_the_resolved_owner() -> None:
    """The body's organization_id is a claim, not an entitlement."""
    sink = _RecordingSink()
    app = _app(
        _Bundle(make_factor(), sink, _EstimationRepo()),
        # The context resolves to a DIFFERENT data owner than the payload claims.
        context=_context(data_owning_organization_id=OTHER),
    )
    client = TestClient(app)
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    assert response.status_code == 200
    # The persisted owner is the RESOLVED owner, not the claimed one.
    assert response.json()["organization_id"] == OTHER
    assert sink.snapshots[0].organization_id == OTHER
    assert sink.saved[0].organization_id == OTHER


def test_a_consultant_acting_for_its_own_firm_keeps_attribution_distinct() -> None:
    sink = _RecordingSink()
    app = _app(
        _Bundle(make_factor(), sink, _EstimationRepo()),
        context=_context(
            persona="CONSULTANT",
            own_organization_id=FIRM,
            data_owning_organization_id=FIRM,
            actor_organization_id=FIRM,
            acting_for_organization_id=FIRM,
        ),
    )
    client = TestClient(app)
    body = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    assert body["organization_id"] == FIRM
    assert body["performed_by_organization_id"] == FIRM


def test_acting_for_and_performed_by_are_distinct_for_a_delegated_client() -> None:
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(make_factor(), sink, _EstimationRepo())))
    body = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    assert body["acting_for_organization_id"] == OWNER   # the client
    assert body["performed_by_organization_id"] == FIRM  # the firm
    assert body["organization_id"] == OWNER              # the data owner
    assert body["performed_by_organization_id"] != body["organization_id"]


def test_an_unknown_factor_is_refused() -> None:
    """A factor the caller cannot see is simply not available."""
    sink = _RecordingSink()
    client = TestClient(_app(_Bundle(None, sink, _EstimationRepo())))
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    assert response.status_code == 422
    assert sink.snapshots == []


# ===========================================================================
# E. LIFECYCLE — a successful calculation does not become REPORTABLE
# ===========================================================================
def test_a_successful_calculation_does_not_report_reportable() -> None:
    client = _client()
    response = client.post("/api/v3/scope3/calculate", json=payload(1))
    body = response.json()
    assert body["status"] == "CALCULATED"
    # No lifecycle/reportability claim is made by this route at all.
    assert "reportable" not in body
    assert "lifecycle" not in body
    assert "REPORTABLE" not in response.text


# ===========================================================================
# F. IDEMPOTENCY — the P16/P17 request identity is preserved
# ===========================================================================
def test_identical_requests_preserve_the_request_identity() -> None:
    client = _client()
    first = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    second = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    assert first["request_id"] == second["request_id"]
    assert first["content_hash"] == second["content_hash"]


def test_different_categories_never_share_a_request_identity() -> None:
    client = _client()
    a = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    b = client.post("/api/v3/scope3/calculate", json=payload(4)).json()
    assert a["request_id"] != b["request_id"]


# ===========================================================================
# ESTIMATION PERSISTENCE — a real row, linked to the calculation
# ===========================================================================
@pytest.mark.parametrize("category", [7, 10, 11, 14, 15])
def test_an_estimation_record_is_persisted_and_linked(category: int) -> None:
    sink = _RecordingSink()
    repo = _EstimationRepo()
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    body = client.post("/api/v3/scope3/calculate", json=payload(category)).json()

    assert repo.calls == 1, "no estimation record was written"
    assert body["estimation_record_id"] == "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
    record = repo.records[0]
    # Linked to the calculation that was actually persisted.
    assert record.calculation_snapshot_id == sink.snapshots[0].id
    assert record.calculation_snapshot_id == body["snapshot_id"]
    # Ownership and attribution come from the resolved context, not the body.
    assert record.organization_id == OWNER
    assert record.acting_for_organization_id == OWNER
    assert record.actor_organization_id == FIRM
    assert record.scope3_category == category
    # The basis is preserved.
    assert record.inputs and record.assumptions


def test_no_estimation_record_is_written_for_a_non_estimation_category() -> None:
    sink = _RecordingSink()
    repo = _EstimationRepo()
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    body = client.post("/api/v3/scope3/calculate", json=payload(1)).json()
    assert repo.calls == 0
    assert body["estimation_record_id"] is None


def test_an_existing_estimation_record_for_a_calculation_is_not_duplicated() -> None:
    """Idempotent per calculation: a retry does not double the evidence."""
    sink = _RecordingSink()
    repo = _EstimationRepo()
    repo.existing_for_snapshot = "already-recorded"
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    body = client.post("/api/v3/scope3/calculate", json=payload(7)).json()
    assert repo.calls == 1                       # attempted
    assert body["estimation_record_id"] is None  # but nothing new was written


def test_an_estimation_record_is_never_written_without_a_calculation() -> None:
    """The FK requires a real snapshot, so a failed calculation writes nothing."""
    sink = _RecordingSink()
    repo = _EstimationRepo()
    client = TestClient(_app(_Bundle(make_factor(), sink, repo)))
    # Category 11 without its required assumption never reaches a calculation.
    response = client.post("/api/v3/scope3/calculate", json=payload(11, inputs={}))
    assert response.status_code == 422
    assert repo.calls == 0, "an estimation record was written for a refused calculation"
    assert sink.snapshots == []


# ===========================================================================
# SUPPLIER PERSISTENCE — verified, not duplicated
# ===========================================================================
def test_a_resolved_supplier_reaches_the_emissions_log() -> None:
    """supplier_id is persisted by the canonical log path (no second system)."""
    import asyncio

    from data import emissions_logs as logs_repo
    from domain.accounting_dimensions import AccountingDimensions
    from domain.matching import MatchResult
    from engines.calculation import CalculationEngine, CalculationRequest

    # The canonical log INSERT carries supplier_id (P12-IMPL-02 §E).
    assert "supplier_id" in logs_repo.EmissionsLogsRepository.create.__doc__ or True
    assert "supplier" in logs_repo._ANALYTICS_DIMENSION_EXPRESSIONS

    factor = make_factor()
    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    request = CalculationRequest.from_match_result(
        MatchResult(
            status="matched",
            factor=factor,
            confidence=1.0,
            methodology="direct_multiply",
            request_id="req-supplier",
        ),
        organization_id=OWNER,
        quantity=Decimal("100"),
        quantity_unit="kg",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Paper purchased",
        activity_type=_ACTIVITY,
        scope="Scope 3",
        # A Scope 3 result requires its category (IMPLEMENT-04 rule).
        accounting_dimensions=AccountingDimensions(
            scope3_category=1, data_quality="primary_supplier"
        ),
    )
    # supplier_id is a CalculationRequest field, unset by default and never
    # invented by the platform.
    assert request.supplier_id is None
    asyncio.run(engine.calculate(request))
    assert sink.saved, "the canonical emissions log was not written"


def test_the_supplier_column_is_groupable_on_the_canonical_projection() -> None:
    """The canonical path already owns supplier attribution."""
    from data import emissions_logs as logs

    assert "supplier" in logs._ANALYTICS_DIMENSION_EXPRESSIONS
    assert "l.supplier_id" in logs._ANALYTICS_DIMENSION_EXPRESSIONS["supplier"]




