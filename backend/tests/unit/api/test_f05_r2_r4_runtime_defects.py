"""CT-FINAL-01 · F-05-R2 / F-05-R4 — the runtime 500s the repoint surfaced.

CT-VERIFY-05 §6 confirmed three pre-existing 500s that the CT-IMPLEMENT-04 embed
repoint made reachable again, plus the related NULL-relation AttributeError:

* **F-05-R2.1** PDF report generation —
  ``FPDF.set_fill_color() takes from 2 to 4 positional arguments but 6 were
  given`` (``report_generator.py``, alternating table-row shading).
* **F-05-R2.2** ``GET /api/organizations/{org_id}/organization-activity`` —
  ``42703 column users_1.raw_user_meta_data does not exist``. The same embed also
  selected ``organization_members.joined_at``, which the canonical schema does
  not define either (init schema: ``id, organization_id, user_id, role,
  created_at, is_active, updated_at``).
* **F-05-R2.3** ``GET /api/organizations/data/{org_id}/emissions-data`` —
  response-model validation error: the declared model requires
  ``organization_id`` and ``summary``; the handler returned only
  ``{records, total}``.
* **F-05-R4** a NULL embedded relation (``assets``) raised ``AttributeError`` on
  the own-tenant read path.

Everything here is DB-free. The service-role client is replaced by fakes that
mimic supabase-py (``maybe_single`` → row dict or ``None``) and PostgREST
(unknown column → ``42703``), so a re-introduced non-existent column fails the
suite instead of a user's request.
"""
from __future__ import annotations

import ast
import asyncio
import pathlib
import re

import pytest
from pydantic import ValidationError

from routes.organizations import dashboard as dashboard_module
from routes.organizations import data as data_module
from routes.organizations.data import EmissionsResponse
from tests.unit.api.fakes import member_user

ORG_A = "org-a"
BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Canonical columns (supabase/migrations/00000000000000_init_schema.sql)
# ---------------------------------------------------------------------------
CANONICAL_COLUMNS = {
    "organization_members": {
        "id",
        "organization_id",
        "user_id",
        "role",
        "created_at",
        "is_active",
        "updated_at",
    },
    "users": {
        "id",
        "email",
        "password_hash",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "email_verified",
        "last_login",
        "created_at",
        "updated_at",
        "is_anonymised",
    },
}

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class PostgrestColumnError(RuntimeError):
    """Mirrors PostgREST's ``42703`` answer for a non-existent column."""


def _assert_columns_are_canonical(select_text: str, table: str) -> None:
    """Raise ``42703`` for any selected column the canonical schema lacks."""
    outer_part, _, embed_part = select_text.partition("(")
    outer = {
        token
        for token in _IDENT.findall(outer_part)
        if token not in {"inner", "left", "users"}
    }
    if table in CANONICAL_COLUMNS:
        unknown = outer - CANONICAL_COLUMNS[table]
        if unknown:
            raise PostgrestColumnError(
                f"42703 column {table}.{sorted(unknown)[0]} does not exist"
            )
    # Only the ``users`` embed is schema-validated here: it is the one whose
    # columns were wrong. Delegated embeds (assets, emission_factors) keep their
    # own tables, which this helper does not model.
    if embed_part and "users" in outer_part:
        unknown = set(_IDENT.findall(embed_part)) - CANONICAL_COLUMNS["users"]
        if unknown:
            raise PostgrestColumnError(
                f"42703 column users_1.{sorted(unknown)[0]} does not exist"
            )



class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal supabase-py query builder with truthful ``maybe_single``."""

    def __init__(self, world, table):
        self.world = world
        self.table = table
        self.select_text = ""
        self.filters = []
        self.single = False
        self.embed_users = False

    def select(self, text="*", **kwargs):
        self.select_text = text
        _assert_columns_are_canonical(text, self.table)
        self.embed_users = "users" in text
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def gte(self, key, value):
        return self

    def lte(self, key, value):
        return self

    def order(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def limit(self, count):
        return self

    def maybe_single(self):
        self.single = True
        return self

    def execute(self):
        if self.table == "organization_members":
            rows = list(self.world.members)
        elif self.table == "organizations":
            rows = list(self.world.organizations)
        elif self.table == "emissions_logs":
            rows = list(self.world.emissions)
        else:
            raise AssertionError(f"unexpected table {self.table}")
        for key, value in self.filters:
            rows = [r for r in rows if r.get(key) == value]
        if self.embed_users:
            rows = [
                {**row, "users": self.world.user_by_id(row.get("user_id"))}
                for row in rows
            ]
        if self.single:
            # supabase-py 2.9.0: an empty ``maybe_single`` yields None.
            return _Result(rows[0]) if rows else None
        return _Result(rows)


class FakeWorld:
    """In-memory tables that reject non-canonical columns (PostgREST parity)."""

    def __init__(self):
        self.members = [
            {
                "id": "member-1",
                "organization_id": ORG_A,
                "user_id": "u-owner",
                "role": "owner",
                "created_at": "2026-09-01T10:00:00Z",
            }
        ]
        self.users = [
            {
                "id": "u-owner",
                "email": "owner@carbontally.test",
                "first_name": "Ada",
                "last_name": "Lovelace",
            }
        ]
        self.organizations = [{"id": ORG_A, "name": "Org A"}]
        # One row with an embedded factor and a NULL asset relation (F-05-R4).
        self.emissions = [
            {
                "id": "log-1",
                "organization_id": ORG_A,
                "start_date": "2026-06-01",
                "end_date": None,
                "raw_quantity": 1000,
                "calculated_kg_co2e": 183.0,
                "metadata": {"scope": "1", "unit": "kWh"},
                "created_at": "2026-06-02T00:00:00Z",
                "assets": None,
                "emission_factors": {
                    "activity_type": "Natural gas",
                    "co2e_multiplier": 0.183,
                },
            },
            {
                "id": "log-2",
                "organization_id": ORG_A,
                "start_date": "2026-07-01",
                "end_date": None,
                "raw_quantity": 10,
                "calculated_kg_co2e": 20.0,
                "metadata": {"scope": "2"},
                "created_at": "2026-07-02T00:00:00Z",
                "assets": {"name": "Boiler"},
                "emission_factors": None,
            },
        ]

    def user_by_id(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                return dict(user)
        return None

    def from_(self, table):
        return _Query(self, table)


def _owner():
    return member_user(ORG_A, "u-owner", "owner@carbontally.test")


# ---------------------------------------------------------------------------
# F-05-R2.1 — PDF table shading must not raise
# ---------------------------------------------------------------------------
def test_r2_1_add_data_table_does_not_raise_type_error():
    from report_generator import EnhancedSustainabilityReportPDF

    pdf = EnhancedSustainabilityReportPDF("Org A", 2025)
    pdf.add_page()
    # Two rows so both branches of the alternating fill run; highlight_best
    # exercises the highlighted-row branch as well.
    pdf.add_data_table(
        ["Activity", "kg CO2e"],
        [["Natural gas", "1,000"], ["Electricity", "500"]],
        highlight_best=True,
    )
    assert pdf.output()  # a real PDF was produced


def test_r2_1_no_set_fill_color_call_passes_more_than_three_channels():
    """Static guard: FPDF accepts 1 or 3 channel arguments, never 5."""
    offenders = []
    for path in sorted(BACKEND_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "tests" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - defensive
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else None
            if name != "set_fill_color":
                continue
            if any(isinstance(arg, ast.Starred) for arg in node.args):
                continue
            if len(node.args) > 3:
                offenders.append(
                    f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} "
                    f"({len(node.args)} args)"
                )
    assert offenders == [], "set_fill_color called with too many channels: " + ", ".join(
        offenders
    )


# ---------------------------------------------------------------------------
# F-05-R2.2 — organization-activity must not select non-existent columns
# ---------------------------------------------------------------------------
def test_r2_2_activity_route_returns_200_with_the_canonical_schema(monkeypatch):
    world = FakeWorld()
    monkeypatch.setattr(dashboard_module, "get_supabase_client", lambda: world)

    payload = asyncio.run(
        dashboard_module.get_organization_activity(
            ORG_A, days=30, current_user=_owner()
        )
    )

    assert payload["organization_id"] == ORG_A
    types = {activity["type"] for activity in payload["activities"]}
    assert types == {"emission_added", "member_joined"}

    member = next(a for a in payload["activities"] if a["type"] == "member_joined")
    assert member["details"]["email"] == "owner@carbontally.test"
    assert member["details"]["full_name"] == "Ada Lovelace"
    assert member["timestamp"] == "2026-09-01T10:00:00Z"

    # F-05-R4: the NULL asset relation is reported as absent, not as a crash —
    # the other row's asset is still read.
    assets = {
        activity["details"]["asset"]
        for activity in payload["activities"]
        if activity["type"] == "emission_added"
    }
    assert assets == {None, "Boiler"}


def test_r2_2_fake_rejects_the_original_broken_select():
    """Sensitivity control: the fake raises 42703 for the pre-fix columns."""
    with pytest.raises(PostgrestColumnError) as exc:
        _assert_columns_are_canonical(
            "id, role, joined_at, users!inner (email, raw_user_meta_data)",
            "organization_members",
        )
    assert "42703" in str(exc.value)

    # ... and the fixed select passes the same guard without raising.
    _assert_columns_are_canonical(
        "id, role, created_at, users!inner (email, first_name, last_name)",
        "organization_members",
    )


def _activity_route_select_literals() -> list:
    """Every string literal used by the ``get_organization_activity`` route."""
    path = BACKEND_ROOT / "routes" / "organizations" / "dashboard.py"
    source = path.read_text()
    literals = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_organization_activity":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    literals.append(sub.value)
    return literals


def test_r2_2_route_does_not_use_non_existent_organization_member_columns():
    """Static guard on the activity route's select statements."""
    selected = "\n".join(_activity_route_select_literals())
    assert selected, "the activity route must select its columns explicitly"
    assert "joined_at" not in selected, "organization_members has no joined_at column"
    assert "raw_user_meta_data" not in selected, "public.users has no metadata column"
    assert "first_name" in selected and "last_name" in selected


# ---------------------------------------------------------------------------
# F-05-R2.3 — the emissions-data payload must satisfy its own response model
# ---------------------------------------------------------------------------
def test_r2_3_emissions_data_payload_satisfies_the_response_model(monkeypatch):
    world = FakeWorld()
    monkeypatch.setattr(data_module, "get_supabase_client", lambda: world)

    payload = asyncio.run(
        data_module.get_organization_emissions(
            ORG_A,
            start_date=None,
            end_date=None,
            scope=None,
            asset_id=None,
            activity_type=None,
            current_user=_owner(),
        )
    )

    validated = EmissionsResponse.model_validate(payload)
    assert validated.organization_id == ORG_A
    assert validated.organization_name == "Org A"
    assert validated.summary.total_records == 2
    assert validated.summary.total_kg_co2e == 203.0
    assert validated.total == 2
    # F-05-R4: the NULL asset relation becomes None, and the embedded factor is
    # still read for the row that has one.
    assert [record.asset for record in validated.records] == [None, "Boiler"]
    assert validated.records[0].activity_type == "Natural gas"
    assert validated.records[0].tonnes_co2e == pytest.approx(0.183)


def test_r2_3_the_original_payload_shape_fails_the_model():
    """Sensitivity control: the pre-fix payload could never satisfy the model."""
    with pytest.raises(ValidationError):
        EmissionsResponse.model_validate({"records": [], "total": 0})


def test_r4_summary_tolerates_a_null_asset_relation():
    summary = data_module.calculate_emissions_summary(
        [
            {
                "calculated_kg_co2e": 10,
                "assets": None,
                "metadata": {"scope": "1"},
                "start_date": "2026-01-05",
            }
        ]
    )
    assert summary.by_asset == {"Unknown": 10}
    assert summary.by_scope == {"1": 10}
    assert summary.by_month == {"2026-01": 10}


