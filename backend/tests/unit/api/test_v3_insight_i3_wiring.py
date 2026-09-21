"""I3 remediation — REAL repository-wiring regression (OHD D-01 / D-02).

The original I3 suite injected a duck-typed bundle, so it could not fail when the
production `RepositoryBundle` lacked the `disclosure_projection` repository
(OHD D-01). These tests exercise the **real construction path**: the actual
`RepositoryBundle` built by `api.dependencies.get_repositories()` with the real
repository classes (only the pool provider is stubbed, so no database is used),
and every read the evidence tool performs is replaced on those real instances.
"""
from __future__ import annotations

import dataclasses
import inspect
from datetime import date
from decimal import Decimal

import pytest

from api import dependencies as deps
from auth import AuthUser
from data.disclosure_projection import DisclosureProjectionRepository
from domain.insight_tool import ToolStatus
from services import insight_tools

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
V2 = "33333333-4444-4555-8666-777777777777"
S1 = "44444444-5555-4666-8777-888888888888"
LINE1 = "55555555-6666-4777-8888-999999999999"

#: The attributes the I3 tool layer resolves. This set is the regression: the
#: real bundle must provide every one of them (it did not provide
#: `disclosure_projection` before the D-01 remediation).
REQUIRED_REPOSITORIES = (
    "reports",
    "report_versions",
    "disclosure_projection",
    "logs",
    "organizations",
    "staff",
    "consultants",
)


class _Pool:
    """Sentinel pool: AbstractRepository only rejects ``None``."""


@pytest.fixture()
async def real_bundle(monkeypatch):
    """The REAL bundle from the REAL factory, with the pool provider stubbed."""

    async def _fake_pool():
        return _Pool()

    monkeypatch.setattr(deps, "get_pool", _fake_pool)
    return await deps.get_repositories()


def test_real_bundle_declares_every_repository_the_tool_layer_uses():
    names = {f.name for f in dataclasses.fields(deps.RepositoryBundle)}
    missing = [name for name in REQUIRED_REPOSITORIES if name not in names]
    assert missing == [], f"RepositoryBundle is missing: {missing}"


def test_real_factory_constructs_every_required_repository():
    source = inspect.getsource(deps.get_repositories)
    missing = [name for name in REQUIRED_REPOSITORIES if f"{name}=" not in source]
    assert missing == [], f"get_repositories() does not construct: {missing}"


def test_service_module_imports_without_an_api_cycle():
    """OHD D-02: the service must import standalone (no api.* at import time)."""
    source = inspect.getsource(insight_tools)
    assert "if TYPE_CHECKING:" in source
    assert "from api.dependencies import RepositoryBundle" not in source.split("if TYPE_CHECKING:")[0]
    assert "authorize_insight_scope  # deferred" in source


async def test_evidence_tool_runs_through_the_real_repository_bundle(real_bundle, monkeypatch):
    assert isinstance(real_bundle.disclosure_projection, DisclosureProjectionRepository)
    calls: list[str] = []

    async def _context(version_id):
        calls.append("report_context")
        return {"organization_id": ORG_A, "report_id": "r-1", "status": "FINAL", "reporting_year": 2025}

    async def _lines(*, report_version_id):
        calls.append("value_lines")
        return [{"disclosure_value_id": "dv-1", "requirement_version_id": "rv-1",
                 "calculation_snapshot_id": S1, "evidence_line_item_id": LINE1, "line_number": 1,
                 "materialisation_kind": "FORWARD", "raw_description": "SECRET RAW TEXT",
                 "raw_quantity": Decimal("2559.0"), "raw_unit": "kWh", "source_page": 3}]

    async def _coverage(*, disclosure_value_id):
        calls.append("evidence_coverage")
        return {"reference_count": 2, "line_linked_count": 1, "snapshot_linked_count": 1}

    async def _staff(user_id):
        return None

    async def _memberships(user_id):
        return []

    async def _org(org_id):
        return type("O", (), {"id": org_id, "is_active": org_id == ORG_A})()

    monkeypatch.setattr(real_bundle.disclosure_projection, "report_context", _context)
    monkeypatch.setattr(real_bundle.disclosure_projection, "value_lines", _lines)
    monkeypatch.setattr(real_bundle.disclosure_projection, "evidence_coverage", _coverage)
    monkeypatch.setattr(real_bundle.staff, "get_by_user", _staff)
    monkeypatch.setattr(real_bundle.consultants, "get_active_memberships_by_user", _memberships)
    monkeypatch.setattr(real_bundle.organizations, "get_by_id", _org)

    user = AuthUser(user_id=ALICE, email="alice@example.test", role="org_owner",
                    role_name="org_owner", organization_id=ORG_A, is_org_member=True)

    result = await insight_tools.invoke_tool(
        tool_name="report_evidence_lookup", current_user=user, repos=real_bundle,
        organization_id=ORG_A, tool_input={"report_version_id": V2},
    )
    assert result.status is ToolStatus.SUCCESS
    line = result.data["lines"][0]
    assert line["evidence_line_item_id"] == LINE1 and line["line_number"] == 1
    for forbidden in ("raw_description", "raw_quantity", "raw_unit", "source_page"):
        assert forbidden not in line
    assert {"kind": "evidence_line_item", "id": LINE1} in [r.as_dict() for r in result.references]
    assert real_bundle.reports.get_full.__self__ is real_bundle.reports  # real instance, untouched
    assert set(calls) <= {"report_context", "value_lines", "evidence_coverage"}

    again = await insight_tools.invoke_tool(
        tool_name="report_evidence_lookup", current_user=user, repos=real_bundle,
        organization_id=ORG_A, tool_input={"report_version_id": V2},
    )
    assert result.as_dict() == again.as_dict()  # deterministic


async def test_evidence_tool_denials_through_the_real_bundle(real_bundle, monkeypatch):
    async def _none(version_id):
        return None

    async def _no_lines(*, report_version_id):
        return []

    async def _staff(user_id):
        return None

    async def _memberships(user_id):
        return []

    async def _org(org_id):
        return type("O", (), {"id": org_id, "is_active": True})()

    monkeypatch.setattr(real_bundle.disclosure_projection, "report_context", _none)
    monkeypatch.setattr(real_bundle.disclosure_projection, "value_lines", _no_lines)
    monkeypatch.setattr(real_bundle.staff, "get_by_user", _staff)
    monkeypatch.setattr(real_bundle.consultants, "get_active_memberships_by_user", _memberships)
    monkeypatch.setattr(real_bundle.organizations, "get_by_id", _org)

    user = AuthUser(user_id=ALICE, email="alice@example.test", role="org_owner",
                    role_name="org_owner", organization_id=ORG_A, is_org_member=True)
    no_data = await insight_tools.invoke_tool(
        tool_name="report_evidence_lookup", current_user=user, repos=real_bundle,
        organization_id=ORG_A, tool_input={"report_version_id": "missing"})
    assert no_data.status is ToolStatus.NO_DATA

    async def _foreign(version_id):
        return {"organization_id": ORG_B, "report_id": "r-b", "status": "FINAL", "reporting_year": 2025}

    monkeypatch.setattr(real_bundle.disclosure_projection, "report_context", _foreign)
    denied = await insight_tools.invoke_tool(
        tool_name="report_evidence_lookup", current_user=user, repos=real_bundle,
        organization_id=ORG_A, tool_input={"report_version_id": V2})
    assert denied.status is ToolStatus.NOT_AUTHORIZED
    assert denied.data == {} and denied.references == ()

    async def _suspended(org_id):
        return type("O", (), {"id": org_id, "is_active": False})()

    monkeypatch.setattr(real_bundle.organizations, "get_by_id", _suspended)
    suspended = await insight_tools.invoke_tool(
        tool_name="report_evidence_lookup", current_user=user, repos=real_bundle,
        organization_id=ORG_A, tool_input={"report_version_id": V2})
    assert suspended.status is ToolStatus.NOT_AUTHORIZED
