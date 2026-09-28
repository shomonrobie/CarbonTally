"""CT-REMEDIATE-01 — the enhanced-report request path: D-1, D-4, and its exits.

CT-VERIFY-06 §6 filed four defects on the enhanced-report surface. They are all
on one request path — ``POST /api/reports/generate-enhanced-report`` — plus the
tenant emissions read that feeds it:

* **D-1** ``GET /api/{org_id}/emissions`` — PostgREST answers SQL ``NULL`` for an
  embedded relation that does not exist (and for a legitimately ``NULL`` column
  such as ``metadata``). Reading ``.get()`` on that ``None`` raised
  ``AttributeError: 'NoneType' object has no attribute 'get'``, so an
  organisation's *own* emissions read answered **HTTP 500**.
* **D-4** ``EnhancedSustainabilityReportGenerator.generate_enhanced_secr_report``
  — fpdf2 2.8.x returns the document as a ``bytearray`` from ``FPDF.output()``,
  so the historical ``.encode('latin-1')`` raised for **every** report request
  and no report was ever produced.
* **D-4-EXT** the year-over-year arrows (``↓↓ ↑↑ ↓ ↑ →``) are outside the core
  Helvetica encoding, so any report with a previous year aborted with
  ``FPDFUnicodeEncodingException`` unless the glyphs are sanitised.
* **D-4-EXT2** ``add_narrative_box`` sized its box through a PyFPDF-only
  ``get_string_height`` helper this module never defined, so the
  year-over-year narrative path aborted with ``AttributeError`` — independently
  of D-4.

and one security hole on the same handler:

* **D-4-AUTH** the handler reads emissions with the **service-role** client for
  whatever ``organization_id`` the *body* names, while ``require_org_member()``
  only enforces scope for organisations named in the route *path*. Without a
  body-scope check, any authenticated member could request another
  organisation's report. ``auth.enforce_org_body_scope`` closes it.

Everything here is DB-free. The service-role client is replaced by an in-memory
world that mirrors the PostgREST surface these handlers use
(``select``/``eq``/``gte``/``lte``/``contains``/``range``/``maybe_single``), so a
regression fails this suite instead of a user's request.
"""
from __future__ import annotations

import asyncio
import ast
import base64
import pathlib

import pytest
from fastapi import FastAPI, HTTPException, status
from starlette.testclient import TestClient

import auth
import report_generator as rg
import routes.emissions as emissions_module
import routes.legacy_reports as legacy_reports
import routes.reports as reports_module
from auth import AuthUser
from fpdf import FPDF
from tests.unit.api.fakes import member_user
from tests.unit.api.route_paths import effective_routes

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]
REPORT_YEAR = 2024
CANONICAL_PATH = "/api/reports/generate-enhanced-report"
LEGACY_PATH = "/api/generate-enhanced-report"


# ---------------------------------------------------------------------------
# In-memory PostgREST surface (service-role client stand-in)
# ---------------------------------------------------------------------------
class _Result:
    """The slice of a PostgREST response body these handlers read."""

    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _Query:
    """Minimal supabase-py query builder with truthful ``maybe_single``."""

    def __init__(self, world, table):
        self.world = world
        self.table = table
        self.filters = []
        self.single = False
        self.window = None
        self.count_mode = None

    def select(self, columns="*", **kwargs):
        self.count_mode = kwargs.get("count")
        return self

    def eq(self, key, value):
        self.filters.append(("eq", key, value))
        return self

    def gte(self, key, value):
        self.filters.append(("gte", key, value))
        return self

    def lte(self, key, value):
        self.filters.append(("lte", key, value))
        return self

    def contains(self, key, value):
        self.filters.append(("contains", key, value))
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, start, end):
        self.window = (start, end)
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        rows = self.world.rows(self.table, self.filters)
        if self.count_mode == "exact":
            return _Result(rows, count=len(rows))
        if self.single:
            # supabase-py 2.9.0: an empty ``maybe_single`` yields None.
            return _Result(rows[0]) if rows else None
        if self.window:
            start, end = self.window
            rows = rows[start:end + 1]
        return _Result(rows)


class EnhancedReportWorld:
    """The rows these handlers read, keyed by table."""

    def __init__(self, emissions=None, metadata=None):
        self.reads = []
        self.organization_members = [
            {
                "id": "member-a",
                "organization_id": ORG_A,
                "user_id": "u-owner-a",
                "role": "owner",
                "is_active": True,
            }
        ]
        self.organizations = [
            {
                "id": ORG_A,
                "name": "Org A Ltd",
                "company_number": "01234567",
                "logo_url": None,
                "industry": "Manufacturing",
                "sector": "Industrial",
            }
        ]
        self.organization_metadata = [
            {
                "organization_id": ORG_A,
                "total_employees": 120,
                "annual_revenue": 4_500_000,
                "total_floor_area_sqft": 25_000,
            }
            if metadata is None
            else metadata
        ]
        self.emissions_logs = current_year_rows() if emissions is None else emissions

    # -- helpers ----------------------------------------------------------
    def add_previous_year(self):
        """Give the organisation a previous reporting year (Year-over-Year)."""
        self.emissions_logs = self.emissions_logs + previous_year_rows()
        return self

    @staticmethod
    def _matches(row, op, key, value):
        actual = row.get(key)
        if op == "eq":
            return actual == value
        if op == "gte":
            return actual is not None and str(actual) >= str(value)
        if op == "lte":
            return actual is not None and str(actual) <= str(value)
        if op == "contains":
            return isinstance(actual, dict) and all(
                actual.get(k) == v for k, v in (value or {}).items()
            )
        raise AssertionError(f"unsupported operator {op}")

    def rows(self, table, filters=()):
        self.reads.append(table)
        rows = [dict(row) for row in (getattr(self, table, None) or [])]
        for op, key, value in filters:
            rows = [row for row in rows if self._matches(row, op, key, value)]
        return rows

    def from_(self, table):
        return _Query(self, table)


class ClientFactory:
    """Records how many times a handler built a service-role client."""

    def __init__(self, client):
        self.client = client
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.client


class BoomClient:
    """Sentinel client — any read at all proves a guard did not run."""

    def __init__(self, label="service-role"):
        self.label = label

    def from_(self, table):
        raise AssertionError(f"{self.label} read of {table} reached the database")


# ---------------------------------------------------------------------------
# Fixture rows
# ---------------------------------------------------------------------------
def current_year_rows():
    """Reporting-year rows, including both D-1 NULL shapes."""
    return [
        {
            "id": "log-cur-1",
            "organization_id": ORG_A,
            "start_date": f"{REPORT_YEAR}-03-31",
            "end_date": f"{REPORT_YEAR}-03-31",
            "raw_quantity": 100000.0,
            "calculated_kg_co2e": 18300.0,
            "metadata": {"scope": "Scope 1", "unit": "kWh"},
            "assets": {
                "id": "asset-1",
                "name": "Boiler 1",
                "type": "Boiler",
                "facility_id": "fac-1",
                "facilities": {"id": "fac-1", "name": "Birmingham Head Office"},
            },
            "emission_factors": {
                "id": "ef-1",
                "activity_type": "Natural Gas",
                "co2e_multiplier": 0.183,
                "reporting_year": REPORT_YEAR,
            },
        },
        {
            "id": "log-cur-2",
            "organization_id": ORG_A,
            "start_date": f"{REPORT_YEAR}-06-30",
            "end_date": f"{REPORT_YEAR}-06-30",
            "raw_quantity": 50000.0,
            "calculated_kg_co2e": 11700.0,
            "metadata": None,          # D-1: legitimately NULL column
            "assets": None,            # D-1: NULL embedded relation
            "emission_factors": None,
        },
    ]


def previous_year_rows():
    """40 t against the current 30 t is a 25 % fall: the strongest down arrow."""
    return [
        {
            "id": "log-prev-1",
            "organization_id": ORG_A,
            "start_date": f"{REPORT_YEAR - 1}-05-31",
            "end_date": f"{REPORT_YEAR - 1}-05-31",
            "raw_quantity": 200000.0,
            "calculated_kg_co2e": 40000.0,
            "metadata": {"scope": "Scope 1"},
            "assets": None,
            "emission_factors": None,
        },
    ]


# ---------------------------------------------------------------------------
# Callers and request bodies
# ---------------------------------------------------------------------------
def owner_a():
    return member_user(ORG_A, "u-owner-a", "owner-a@carbontally.test")


def member_b():
    return member_user(ORG_B, "u-owner-b", "owner-b@carbontally.test")


def report_body(organization_id: str = ORG_A, report_type: str = "SECR"):
    return {
        "organization_id": organization_id,
        "reporting_year": REPORT_YEAR,
        "report_type": report_type,
        "include_narratives": True,
    }


def build_app(*routers, user=None, unauthenticated=False):
    """A test app whose ``get_current_user`` is asserted, not re-authenticated."""
    app = FastAPI()
    for router in routers:
        app.include_router(router)

    if unauthenticated:

        async def deny():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        app.dependency_overrides[auth.get_current_user] = deny
    elif user is not None:
        app.dependency_overrides[auth.get_current_user] = lambda: user
    return app


def decode_pdf(body) -> bytes:
    return base64.b64decode(body["pdf_base64"])


# ---------------------------------------------------------------------------
# Static-source helpers (guards that survive a refactor of the handler bodies)
# ---------------------------------------------------------------------------
def module_functions(path: pathlib.Path):
    tree = ast.parse(path.read_text())
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def literal_first_args(func, attr):
    """Literal first arguments of every ``<something>.<attr>(...)`` call."""
    found = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != attr:
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            found.append(node.args[0].value)
    return found


# ---------------------------------------------------------------------------
# D-1 — NULL relations and NULL metadata in the tenant emissions read
# ---------------------------------------------------------------------------
def test_d1_emissions_read_survives_null_asset_and_null_metadata(monkeypatch):
    """`GET /api/{org_id}/emissions` must answer with the rows it has.

    Before the fix the handler called ``.get()`` on the ``None`` PostgREST
    returns for a missing embedded relation, and again on a legitimately NULL
    ``metadata`` column, so the organisation's own read was an HTTP 500.
    """
    world = EnhancedReportWorld()
    monkeypatch.setattr(emissions_module, "get_supabase_client", lambda: world)

    payload = asyncio.run(
        emissions_module.get_emissions_for_organization(
            ORG_A,
            limit=100,
            offset=0,
            # FastAPI resolves ``Query`` sentinels only through the dependency
            # system, so a direct in-process call must pass the filter defaults
            # explicitly — otherwise the truthy ``Query(None)`` sentinel is
            # treated as a real ``start_date``/``scope`` and the read comes back
            # empty. The HTTP test below exercises the resolved path.
            start_date=None,
            end_date=None,
            scope=None,
            asset_id=None,
            current_user=owner_a(),
        )
    )

    assert payload["success"] is True
    assert payload["organization_id"] == ORG_A
    assert world.reads.count("organization_members") == 1
    assert world.reads.count("emissions_logs") == 2  # page query + count query

    rows = {row["id"]: row for row in payload["emissions"]}
    assert set(rows) == {"log-cur-1", "log-cur-2"}

    # The NULL-relation row still reports every contract key, as None.
    null_row = rows["log-cur-2"]
    assert null_row["asset_id"] is None
    assert null_row["asset_name"] is None
    assert null_row["asset_type"] is None
    assert null_row["facility_id"] is None
    assert null_row["facility_name"] is None
    assert null_row["metadata"] is None
    assert null_row["activity_type"] is None
    assert null_row["tonnes_co2e"] == pytest.approx(11.7)

    # ...and the populated row is still joined through assets -> facilities.
    mapped = rows["log-cur-1"]
    assert mapped["asset_name"] == "Boiler 1"
    assert mapped["facility_name"] == "Birmingham Head Office"
    assert mapped["activity_type"] == "Natural Gas"
    assert mapped["co2e_multiplier"] == pytest.approx(0.183)

    # The NULL row contributes to the total but not to any scope bucket.
    assert payload["total"] == 2
    assert payload["summary"]["record_count"] == 2
    assert payload["summary"]["total_kg"] == pytest.approx(30000.0)
    assert payload["summary"]["total_tonnes"] == pytest.approx(30.0)
    assert payload["summary"]["scope_breakdown"]["scope1"] == pytest.approx(18.3)
    assert payload["summary"]["scope_breakdown"]["scope2"] == pytest.approx(0.0)


def test_d1_emissions_route_answers_200_over_http(monkeypatch):
    """The same read through the router: the reported symptom was 500."""
    world = EnhancedReportWorld()
    monkeypatch.setattr(emissions_module, "get_supabase_client", lambda: world)
    app = build_app(emissions_module.router, user=owner_a())

    response = TestClient(app).get(f"/api/{ORG_A}/emissions?limit=100&offset=0")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"]["total_tonnes"] == pytest.approx(30.0)
    assert [row["id"] for row in body["emissions"]] == ["log-cur-1", "log-cur-2"]


def test_d1_control_the_unnormalised_null_relation_still_explodes():
    """Sensitivity control: this is the pre-fix expression, and it still raises.

    If this control ever stops raising, the regression test above has stopped
    proving anything about NULL handling.
    """
    record = dict(current_year_rows()[1])

    def legacy_transform(row):
        asset = row.get("assets")
        facility = asset.get("facilities")          # pre-fix: no `or {}`
        return facility.get("name")

    with pytest.raises(AttributeError, match="NoneType"):
        legacy_transform(record)

    # The guarded expression in the handler tolerates the same row.
    assert (record.get("assets") or {}).get("facilities") is None


def test_d1_static_guard_the_null_relations_are_normalised():
    """Both NULL shapes are normalised at their read sites, not downstream."""
    source = (BACKEND_ROOT / "routes" / "emissions.py").read_text()

    assert "record.get('assets') or {}" in source
    assert "asset.get('facilities') or {}" in source
    assert "record.get('emission_factors') or {}" in source
    assert "(e.get('metadata') or {}).get('scope'" in source


def test_d1_report_generator_survives_the_same_null_metadata_row(monkeypatch):
    """The report path reads the same rows, so it needs the same normalisation.

    ``_generate_emission_sources`` called ``record.get('metadata', {})`` and then
    ``.get('scope')`` on the result; PostgREST's SQL ``NULL`` survives the
    ``default`` argument, so one NULL-``metadata`` row aborted the whole report
    with ``AttributeError`` — the D-1 defect again, one layer down.
    """
    world = EnhancedReportWorld()  # includes the NULL-metadata row
    app = report_app(monkeypatch, world, user=owner_a())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metadata"]["records_used"] == 2  # the NULL row is included
    pdf = decode_pdf(body)
    assert pdf.startswith(b"%PDF-")


def test_d1_report_generator_normalises_metadata_at_the_read_site():
    """Static guard: the guarded read stays guarded."""
    source = (BACKEND_ROOT / "report_generator.py").read_text()

    assert "metadata = record.get('metadata') or {}" in source
    assert "record.get('metadata', {})\n" not in source


# ---------------------------------------------------------------------------
# HTTP harness for the report routes
# ---------------------------------------------------------------------------
def report_app(monkeypatch, world, *, user=None, unauthenticated=False,
               router=None):
    """Mount a report router over the in-memory world.

    ``routes.reports`` includes ``report_generator.router`` at the top of the
    module, so the handler that answers HTTP builds its own service-role client
    through ``report_generator.create_client``, while the shadow copy is reached
    in-process by the POD-5 compatibility layer through
    ``routes.reports.get_supabase_client``. Both are pointed at the world so
    these tests exercise the request path rather than the wiring.
    """
    monkeypatch.setattr(rg, "create_client", lambda *args, **kwargs: world)
    monkeypatch.setattr(reports_module, "get_supabase_client", lambda: world)
    return build_app(
        router if router is not None else reports_module.router,
        user=user,
        unauthenticated=unauthenticated,
    )


# ---------------------------------------------------------------------------
# Route topology — which handler answers the canonical path
# ---------------------------------------------------------------------------
def test_topology_report_generator_owns_the_canonical_path():
    """Two POST handlers are registered for the path; the first registration wins.

    ``routes.reports`` includes ``report_generator.router`` at the top of the
    module, so over HTTP the hardened generator answers the canonical path and
    ``routes.reports``' own copy is only reachable in-process (POD-5 compat).
    FastAPI >= 0.141 defers ``include_router``, so the effective routes are read
    through ``route_paths.effective_routes`` rather than ``route.path`` /
    ``route.endpoint`` on ``app.routes`` entries — those are lazy wrappers there.
    """
    handlers = [
        (endpoint, methods)
        for path, endpoint, methods in effective_routes(reports_module.router)
        if path == CANONICAL_PATH and "POST" in methods
    ]

    assert [endpoint for endpoint, _ in handlers] == [
        rg.generate_enhanced_sustainability_report,
        reports_module.generate_enhanced_sustainability_report,
    ]
    assert [methods for _, methods in handlers] == [
        frozenset({"POST"}),
        frozenset({"POST"}),
    ]


def test_topology_canonical_path_is_served_by_the_generator_module(monkeypatch):
    """Behavioural proof of the order asserted above: the first handler runs.

    The shadow handler's client factory is booby-trapped, so this request can
    only answer 200 if FastAPI dispatched to ``report_generator``'s handler for
    the canonical path. The other HTTP tests in this module patch both clients,
    which makes them tolerant of either handler; this is the test that fails if
    the router includes are re-ordered.
    """
    world = EnhancedReportWorld()
    monkeypatch.setattr(rg, "create_client", lambda *args, **kwargs: world)

    def shadow_handler_used():
        raise AssertionError("the shadow handler answered the canonical path")

    monkeypatch.setattr(reports_module, "get_supabase_client", shadow_handler_used)
    app = build_app(reports_module.router, user=owner_a())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body())

    assert response.status_code == 200, response.text
    assert response.json()["report_type"] == "SECR"
    assert world.reads  # the generator's own client served the report


def test_topology_legacy_compat_delegates_to_the_shadow_handler():
    """``/api/generate-enhanced-report`` reaches the second handler in-process."""
    assert legacy_reports.legacy_reports is reports_module
    assert (
        legacy_reports.legacy_reports.generate_enhanced_sustainability_report
        is reports_module.generate_enhanced_sustainability_report
    )


# ---------------------------------------------------------------------------
# D-4 — the response must carry a real PDF document
# ---------------------------------------------------------------------------
def test_d4_report_route_returns_a_real_pdf_document(monkeypatch):
    """fpdf2 2.8.x ``FPDF.output()`` is a ``bytearray``; the response must be it."""
    world = EnhancedReportWorld()
    app = report_app(monkeypatch, world, user=owner_a())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["report_type"] == "SECR"
    assert body["filename"] == f"SECR_Report_Org A Ltd_{REPORT_YEAR}.pdf"

    pdf = decode_pdf(body)
    assert pdf.startswith(b"%PDF-")
    assert pdf.rstrip().endswith(b"%%EOF")
    assert len(pdf) > 1_000  # a rendered document, not an empty stub

    # The organisation's records and no others were read for the report.
    assert body["metadata"]["records_used"] == 2
    assert body["metadata"]["total_emissions_tonnes"] == pytest.approx(30.0)


def test_d4_control_a_bytearray_has_no_encode():
    """Sensitivity control: the pre-fix expression is exactly what failed.

    ``.encode('latin-1')`` was called on the ``output()`` return value. If this
    control ever stops raising, the assertion above no longer proves anything
    about the bytearray.
    """
    pdf = rg.EnhancedSustainabilityReportPDF("Org A Ltd", REPORT_YEAR)
    pdf.add_page()
    output = pdf.output()

    assert isinstance(output, bytearray), type(output).__name__
    assert not isinstance(output, str)
    with pytest.raises(AttributeError):
        output.encode("latin-1")


def test_d4_report_payload_is_base64_of_pdf_bytes():
    """Static guard: the payload is base64 of the PDF *bytes*."""
    source = (BACKEND_ROOT / "report_generator.py").read_text()

    assert "bytes(pdf.output(" in source
    assert "base64.b64encode(pdf_output)" in source


# ---------------------------------------------------------------------------
# D-4-EXT — the year-over-year arrows must not reach the core font raw
# ---------------------------------------------------------------------------
def test_d4_ext_yoy_report_with_the_down_arrows_is_generated(monkeypatch):
    """A previous year draws ↓↓/↑↑, and those glyphs killed report generation."""
    world = EnhancedReportWorld().add_previous_year()
    app = report_app(monkeypatch, world, user=owner_a())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metadata"]["yoy_change"] == pytest.approx(-25.0)
    assert body["metadata"]["records_used"] == 2  # the current year only
    assert decode_pdf(body).startswith(b"%PDF-")


def test_d4_ext_control_the_raw_arrow_is_outside_the_core_encoding():
    """The arrows are not latin-1, so they cannot go to the core font raw."""
    arrow = rg.generate_trend_arrow(-25.0)
    assert arrow == "↓↓"
    with pytest.raises(UnicodeEncodeError):
        arrow.encode("latin-1")

    sanitised = rg.sanitize_text(arrow)
    assert sanitised.encode("ascii")  # now representable
    assert sanitised != arrow


def test_d4_ext_the_trend_indicator_draws_every_arrow_bucket():
    """The drawing method itself must not raise on any arrow glyph."""
    pdf = rg.EnhancedSustainabilityReportPDF("Org A Ltd", REPORT_YEAR)
    pdf.add_page()
    for percentage in (-25.0, -2.0, 0.0, 2.0, 25.0):
        pdf.add_trend_indicator(percentage)

    assert bytes(pdf.output()).startswith(b"%PDF-")


def test_d4_ext_static_guard_the_arrow_passes_through_sanitize_text():
    source = (BACKEND_ROOT / "report_generator.py").read_text()
    assert 'sanitize_text(f"{arrow}' in source


# ---------------------------------------------------------------------------
# D-4-EXT2 — the narrative box must be sized without PyFPDF's helper
# ---------------------------------------------------------------------------
def test_d4_ext2_the_pdf_class_owns_get_string_height():
    """fpdf2 exposes ``get_string_width`` only; the class must provide its own."""
    assert not hasattr(FPDF, "get_string_height")
    assert "get_string_height" in vars(rg.EnhancedSustainabilityReportPDF)


def test_d4_ext2_narrative_box_draws_a_box_it_measured():
    pdf = rg.EnhancedSustainabilityReportPDF("Org A Ltd", REPORT_YEAR)
    pdf.add_page()
    pdf.add_narrative_box(
        "Analysis", "Emissions fell 25% year on year.", "comparison"
    )
    pdf.add_narrative_box("Methodology", "DEFRA 2024 factors.", "methodology")
    pdf.add_narrative_box("Efficiency", "Boiler replacement.", "efficiency")

    assert bytes(pdf.output()).startswith(b"%PDF-")


def test_d4_ext2_narrative_box_measures_the_width_it_draws():
    """AST guard: the box is measured with its own drawn width (180 mm).

    The pre-fix call passed 20 mm — a tenth of the drawn column — so the box was
    sized for a column that does not exist. The helper it called did not exist
    either (see the guard above).
    """
    functions = module_functions(BACKEND_ROOT / "report_generator.py")
    narrative_box = functions["add_narrative_box"]

    measured = literal_first_args(narrative_box, "get_string_height")
    assert measured == [180]
    assert measured != [20]
    assert 180 in literal_first_args(narrative_box, "multi_cell")


def test_d4_ext2_static_guard_the_narrative_box_uses_the_local_helper():
    source = (BACKEND_ROOT / "report_generator.py").read_text()

    assert "def get_string_height(" in source
    assert "box_height = self.get_string_height(180" in source


# ---------------------------------------------------------------------------
# D-4-AUTH — the body organisation is authorised before any service-role read
# ---------------------------------------------------------------------------
def no_org_user():
    """An authenticated account that carries no organisation context."""
    return AuthUser(
        user_id="u-no-org",
        email="no-org@carbontally.test",
        role="user",
        role_name="user",
        organization_id=None,
        is_org_member=True,
    )


def test_auth_report_route_requires_authentication(monkeypatch):
    """The historical handler served the route with no guard at all."""
    world = EnhancedReportWorld()
    app = report_app(monkeypatch, world, unauthenticated=True)

    response = TestClient(app).post(CANONICAL_PATH, json=report_body())

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
    assert world.reads == []  # no service-role read was attempted


def test_auth_report_route_denies_a_member_of_another_organisation(monkeypatch):
    """Cross-tenant: org B's member asks for org A's report."""
    world = EnhancedReportWorld()
    app = report_app(monkeypatch, world, user=member_b())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body(ORG_A))

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "You don't have access to this organization"
    assert world.reads == []


def test_auth_report_route_denies_an_account_without_an_organisation(monkeypatch):
    world = EnhancedReportWorld()
    app = report_app(monkeypatch, world, user=no_org_user())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body(ORG_A))

    assert response.status_code == 403
    assert response.json()["detail"] == "No organisation context for this account."
    assert world.reads == []


def test_auth_report_route_serves_the_callers_own_organisation(monkeypatch):
    world = EnhancedReportWorld()
    app = report_app(monkeypatch, world, user=owner_a())

    response = TestClient(app).post(CANONICAL_PATH, json=report_body(ORG_A))

    assert response.status_code == 200, response.text
    assert decode_pdf(response.json()).startswith(b"%PDF-")


def test_auth_legacy_compat_path_is_scoped_marked_and_served(monkeypatch):
    """The POD-5 alias authorises the body org, then reaches the shadow handler."""
    world = EnhancedReportWorld()
    app = report_app(
        monkeypatch,
        world,
        user=owner_a(),
        router=legacy_reports.router,
    )
    client = TestClient(app)

    allowed = client.post(LEGACY_PATH, json=report_body(ORG_A))
    assert allowed.status_code == 200, allowed.text
    assert allowed.headers["Deprecation"] == "true"
    assert allowed.headers["Link"] == '</api/v3/reports>; rel="successor-version"'
    assert decode_pdf(allowed.json()).startswith(b"%PDF-")

    reads_before = list(world.reads)
    denied = client.post(LEGACY_PATH, json=report_body(ORG_B))
    assert denied.status_code == 403
    assert world.reads == reads_before  # denied before any service-role read


def test_auth_legacy_compat_path_requires_authentication(monkeypatch):
    world = EnhancedReportWorld()
    app = report_app(
        monkeypatch,
        world,
        unauthenticated=True,
        router=legacy_reports.router,
    )

    response = TestClient(app).post(LEGACY_PATH, json=report_body(ORG_A))

    assert response.status_code == 401
    assert world.reads == []
