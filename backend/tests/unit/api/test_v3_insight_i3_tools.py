"""I3 — controlled read-only Insight tools (registry, execution, authorization).

Authorization: PO I3 Tool Catalogue Ratification Decision Record (2026-09-21).
Covers the ratified verification set (§14): authorization ALLOW/DENY per persona,
organisation-active/subscription state, current-scope reauthorization, forged ids,
tool-boundary enforcement, input validation, output-boundary allowlists, determinism,
reference semantics, status handling, and report lifecycle (§30.3).

In-memory only: the production repositories are replaced through FastAPI dependency
overrides using the same surfaces the real services call. No database is opened.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from api import v3_insight_tools
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CONSULTANT = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
STAFF = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
FIRM = "ffffffff-ffff-4fff-8fff-ffffffffffff"
R1 = "11111111-2222-4333-8444-555555555555"
V1 = "22222222-3333-4444-8555-666666666666"
V2 = "33333333-4444-4555-8666-777777777777"
S1 = "44444444-5555-4666-8777-888888888888"
LINE1 = "55555555-6666-4777-8888-999999999999"
BASE = "/api/v3/insight/tools"


class _Reports:
    def __init__(self):
        self.rows = {}

    def add(self, row):
        self.rows[row["id"]] = row

    async def get_full(self, report_id):
        return self.rows.get(report_id)


class _Versions:
    def __init__(self):
        self.rows = {}

    def add(self, row):
        self.rows[row["id"]] = row

    async def list_for_report(self, report_id):
        rows = [v for v in self.rows.values() if v["report_id"] == report_id]
        return sorted(rows, key=lambda v: -v["version_number"])

    async def get_current(self, report_id):
        return next(
            (v for v in await self.list_for_report(report_id) if v.get("is_current")), None
        )

    async def get(self, version_id):
        return self.rows.get(version_id)

    async def get_by_number(self, report_id, version_number):
        return next(
            (
                v
                for v in self.rows.values()
                if v["report_id"] == report_id and v["version_number"] == version_number
            ),
            None,
        )


class _Projection:
    def __init__(self):
        self.contexts = {}
        self.lines = {}
        self.coverage = {}

    async def report_context(self, report_version_id):
        return self.contexts.get(report_version_id)

    async def value_lines(self, *, report_version_id):
        return self.lines.get(report_version_id, [])

    async def evidence_coverage(self, *, disclosure_value_id):
        return self.coverage.get(disclosure_value_id, {})


class _Logs:
    def __init__(self):
        self.snapshots = {}

    async def get_snapshot(self, snapshot_id):
        return self.snapshots.get(snapshot_id)


class _Staff:
    def __init__(self):
        self.profiles = {}
        self.roles = {}

    def add(self, user_id, *, permissions=None, entity_id=None, is_active=True):
        from domain.staff import StaffProfile, StaffRole

        role_id = f"role-{user_id[:6]}"
        self.roles[role_id] = StaffRole(id=role_id, name="ops", permissions=permissions or {})
        self.profiles[user_id] = StaffProfile(
            id=f"profile-{user_id[:6]}",
            user_id=user_id,
            first_name="S",
            last_name="T",
            email=f"{user_id[:6]}@example.test",
            role_id=role_id,
            is_active=is_active,
            entity_id=entity_id,
        )

    async def get_by_user(self, user_id):
        return self.profiles.get(user_id)

    async def get_role(self, role_id):
        return self.roles.get(role_id)


class _Consultants:
    def __init__(self):
        self.memberships = {}
        self.profiles = {}
        self.grants = {}

    def add_member(self, user_id, firm_id=FIRM, status="active"):
        self.memberships.setdefault(user_id, []).append(
            type("M", (), {"firm_id": firm_id, "joined_at": None, "invited_at": None})()
        )
        self.profiles[firm_id] = type("P", (), {"id": firm_id, "is_active": True})()
        self.grants[(firm_id, status)] = None

    def grant(self, organization_id, status="active"):
        self.grants[(FIRM, organization_id)] = type("G", (), {"status": status})()

    async def get_active_memberships_by_user(self, user_id):
        return self.memberships.get(user_id, [])

    async def get_profile_by_id(self, profile_id):
        return self.profiles.get(profile_id)

    async def get_client_by_org(self, consultant_id, organization_id):
        return self.grants.get((consultant_id, organization_id))


class _Orgs:
    def __init__(self, active=(ORG_A, ORG_B)):
        self.active = set(active)

    async def get_by_id(self, org_id):
        return type("O", (), {"id": org_id, "is_active": org_id in self.active})()


def _user(user_id, organization_id, *, role="org_owner", is_org_member=True, is_staff=False, entity_id=None):
    return AuthUser(
        user_id=user_id,
        email=f"{user_id[:8]}@example.test",
        role=role,
        role_name=role,
        organization_id=organization_id,
        is_org_member=is_org_member,
        is_staff=is_staff,
        entity_id=entity_id,
    )


def _seed():
    reports, versions = _Reports(), _Versions()
    projection, logs = _Projection(), _Logs()
    staff, consultants, orgs = _Staff(), _Consultants(), _Orgs()
    # Report instances. Each carries fields that must NOT be exposed (signed URL,
    # internal actor, unbounded content) so the allowlist is proven by omission.
    reports.add({"id": R1, "organization_id": ORG_A, "report_type": "SECR", "reporting_year": 2025,
                 "report_name": "2025 SECR", "status": "completed", "created_at": "2025-02-01T09:00:00",
                 "completed_at": "2025-02-01T09:30:00", "final_report_url": "https://signed.example/x",
                 "created_by": "internal-actor", "generated_content": {"sections": [1, 2, 3]}, "error_log": "none"})
    reports.add({"id": "report-draft", "organization_id": ORG_A, "report_type": "SECR",
                 "reporting_year": 2025, "report_name": "Draft SECR", "status": "in_progress"})
    reports.add({"id": "report-org-b", "organization_id": ORG_B, "report_type": "SECR",
                 "reporting_year": 2025, "report_name": "Other org", "status": "completed"})
    # Versions (lifecycle vocabulary: DRAFT/REVIEWED/APPROVED/FINAL + is_current).
    versions.add({"id": V1, "report_id": R1, "version_number": 1, "status": "DRAFT", "is_current": False,
                  "created_at": "2025-01-15T09:00:00", "content": {"big": "payload"},
                  "file_url": "https://signed.example/v1", "file_name": "v1.pdf", "created_by": "actor",
                  "notes": "internal note", "change_summary": "internal"})
    versions.add({"id": V2, "report_id": R1, "version_number": 2, "status": "FINAL", "is_current": True,
                  "created_at": "2025-02-01T09:30:00", "file_url": "https://signed.example/v2"})
    versions.add({"id": "version-draft", "report_id": "report-draft", "version_number": 1,
                  "status": "DRAFT", "is_current": True, "created_at": "2025-03-01T09:00:00"})
    versions.add({"id": "version-org-b", "report_id": "report-org-b", "version_number": 1,
                  "status": "FINAL", "is_current": True, "created_at": "2025-04-01T09:00:00"})
    # Disclosure projection (the report-version → evidence path, reused as-is).
    projection.contexts[V2] = {"organization_id": ORG_A, "report_id": R1, "status": "FINAL", "reporting_year": 2025}
    projection.contexts["version-org-b"] = {"organization_id": ORG_B, "report_id": "report-org-b",
                                            "status": "FINAL", "reporting_year": 2025}
    projection.lines[V2] = [{"disclosure_value_id": "dv-1", "requirement_version_id": "rv-1",
                             "calculation_snapshot_id": S1, "evidence_line_item_id": LINE1, "line_number": 1,
                             "materialisation_kind": "FORWARD", "raw_description": "SECRET RAW TEXT",
                             "raw_quantity": Decimal("2559.0"), "raw_unit": "kWh", "source_page": 3}]
    projection.coverage["dv-1"] = {"reference_count": 2, "line_linked_count": 1, "snapshot_linked_count": 1}
    # Authoritative snapshot with the ratified provenance set + internal fields.
    logs.snapshots[S1] = {"id": S1, "organization_id": ORG_A, "activity": "Natural gas", "activity_type": "natural_gas",
                          "quantity": Decimal("2559.0"), "quantity_unit": "kWh", "co2e_multiplier": Decimal("0.1829"),
                          "co2e_kg": Decimal("2469.16978"), "scope": "Scope 1", "date": date(2025, 1, 3),
                          "reporting_year": 2025, "methodology": "direct_multiply", "algorithm_version": "v1",
                          "content_hash": "af640887", "factor_id": "b9d1ed06", "factor_kind": "emission_factor",
                          "customer_factor_id": None, "factor_source": "DEFRA", "source_item_id": "item-1",
                          "source_line_item_id": LINE1, "calculated_by": "internal-actor", "performed_by": "actor",
                          "request_id": "req-1", "import_batch_id": "batch-1", "factor_set": "DEFRA-2025",
                          "source_file": "gas.pdf", "source_page": 3}
    return SimpleNamespace(reports=reports, versions=versions, projection=projection, logs=logs,
                           staff=staff, consultants=consultants, orgs=orgs,
                           # Phase 8 I8-A — shared rate-limit store (in-memory double).
                           insight_limits=InsightLimitsFake())


@pytest.fixture()
def api():
    world = _seed()
    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    state = {"user": _user(ALICE, ORG_A), "unauthenticated": False}

    async def _current_user():
        if state["unauthenticated"]:
            raise HTTPException(status_code=401, detail="Authentication required",
                                headers={"WWW-Authenticate": "Bearer"})
        return state["user"]

    async def _repositories():
        return type("Bundle", (), {"reports": world.reports, "report_versions": world.versions,
                                   "disclosure_projection": world.projection, "logs": world.logs,
                                   "staff": world.staff, "consultants": world.consultants,
                                   "organizations": world.orgs, "insight": None,
                                   # Phase 8 I8-A — the shared rate-limit store double.
                                   "insight_limits": InsightLimitsFake()})()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    return SimpleNamespace(client=TestClient(app), state=state, world=world)


def _invoke(api, tool, tool_input, org=ORG_A):
    return api.client.post(f"{BASE}/invoke", json={"organization_id": org, "tool": tool, "input": tool_input})


def _intent(api, text):
    return api.client.post(f"{BASE}/intent", json={"utterance": text})


# --------------------------------------------------------------------------
# Registry boundary (PO §4) and read-only proof
# --------------------------------------------------------------------------
def test_registry_exposes_the_authorized_tool_catalogue(api):
    """PO I3 four ratified tools + the Phase 8 analytics tools (authorized).

    The ratified four remain first and unchanged; ``insight_discovery``,
    ``insight_aggregation`` and ``insight_aggregate_provenance`` were authorized by
    the PO Insight Discovery-Aggregation-Provenance package (2026-09-22), and
    ``insight_temporal_comparison`` by the PO P2 implementation authorization
    (2026-09-22). Exactly one tool was added by P2.
    """
    body = api.client.get(BASE).json()
    assert [t["name"] for t in body["tools"]] == [
        "report_lookup", "report_version_lookup", "report_evidence_lookup", "calculation_snapshot_lookup",
        "insight_discovery", "insight_aggregation", "insight_aggregate_provenance",
        "insight_temporal_comparison",
    ]
    assert all(t["read_only"] is True for t in body["tools"])
    assert body["contract_version"] == "i3-6point-v1"


def test_registry_declares_the_six_point_contract(api):
    for tool in api.client.get(BASE).json()["tools"]:
        assert tool["purpose"]
        assert tool["authorization"].startswith("i2-boundary")
        assert tool["output_fields"]
        # The analytics tools are totals/identities, not evidence-bearing records,
        # so an empty reference-kind list is a declaration, not an omission.
        if not tool["name"].startswith("insight_"):
            assert tool["reference_kinds"]
        assert tool["statuses"] == ["success", "no_data", "not_authorized", "invalid_input", "error"]


def test_tool_layer_contains_no_mutation_path():
    import inspect

    from services import insight_tools

    source = inspect.getsource(insight_tools)
    for forbidden in ("INSERT INTO", "DELETE FROM", "UPDATE public", "save_snapshot", "create_generation_request", "set_status"):
        assert forbidden not in source, forbidden


# --------------------------------------------------------------------------
# report_lookup
# --------------------------------------------------------------------------
def test_report_lookup_allows_customer_in_own_active_organisation(api):
    body = _invoke(api, "report_lookup", {"report_id": R1}).json()
    assert body["status"] == "success"
    assert body["data"]["current_version"]["status"] == "FINAL"
    assert body["data"]["is_approved_or_final"] is True
    assert {v["version_number"] for v in body["data"]["versions"]} == {1, 2}
    for forbidden in ("final_report_url", "created_by", "generated_content", "error_log"):
        assert forbidden not in body["data"]
    assert {"kind": "report", "id": R1} in body["references"]
    assert {"kind": "report_version", "id": V2} in body["references"]
    assert body["invocation"]["authorization"] == "i2-boundary"


def test_report_lookup_never_presents_a_draft_as_approved(api):
    body = _invoke(api, "report_lookup", {"report_id": "report-draft"}).json()
    assert body["status"] == "success"
    assert body["data"]["current_version"]["status"] == "DRAFT"
    assert body["data"]["is_approved_or_final"] is False


def test_report_lookup_reference_does_not_grant_cross_scope_access(api):
    body = _invoke(api, "report_lookup", {"report_id": "report-org-b"}).json()
    assert body["status"] == "not_authorized"
    assert body["data"] == {}
    assert body["references"] == []


def test_report_lookup_denies_foreign_organisation_request(api):
    assert _invoke(api, "report_lookup", {"report_id": R1}, org=ORG_B).json()["status"] == "not_authorized"


def test_report_lookup_denies_suspended_organisation(api):
    api.world.orgs.active.discard(ORG_A)
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "not_authorized"


def test_report_lookup_no_data_for_unknown_report(api):
    body = _invoke(api, "report_lookup", {"report_id": "missing"}).json()
    assert body["status"] == "no_data" and body["reason"] == "report_not_found"


# --------------------------------------------------------------------------
# report_version_lookup
# --------------------------------------------------------------------------
def test_report_version_lookup_by_id_and_by_number(api):
    by_id = _invoke(api, "report_version_lookup", {"version_id": V2}).json()
    assert by_id["status"] == "success"
    assert by_id["data"]["status"] == "FINAL" and by_id["data"]["is_current"] is True
    for forbidden in ("content", "file_url", "file_name", "created_by", "notes", "change_summary"):
        assert forbidden not in by_id["data"]
    by_number = _invoke(api, "report_version_lookup", {"report_id": R1, "version_number": 1}).json()
    assert by_number["data"]["status"] == "DRAFT"


def test_report_version_lookup_statuses(api):
    assert _invoke(api, "report_version_lookup", {"report_id": R1, "version_number": "abc"}).json()["status"] == "invalid_input"
    assert _invoke(api, "report_version_lookup", {}).json()["status"] == "invalid_input"
    assert _invoke(api, "report_version_lookup", {"version_id": "missing"}).json()["status"] == "no_data"
    assert _invoke(api, "report_version_lookup", {"version_id": "version-org-b"}).json()["status"] == "not_authorized"


# --------------------------------------------------------------------------
# report_evidence_lookup
# --------------------------------------------------------------------------
def test_report_evidence_lookup_returns_references_only(api):
    body = _invoke(api, "report_evidence_lookup", {"report_version_id": V2}).json()
    assert body["status"] == "success"
    line = body["data"]["lines"][0]
    assert line["evidence_line_item_id"] == LINE1 and line["calculation_snapshot_id"] == S1
    assert line["line_number"] == 1
    for forbidden in ("raw_description", "raw_quantity", "raw_unit", "source_page"):
        assert forbidden not in line
    assert body["data"]["coverage"][0]["reference_count"] == 2
    assert body["data"]["report_version"]["status"] == "FINAL"
    assert {"kind": "evidence_line_item", "id": LINE1} in body["references"]
    assert {"kind": "calculation_snapshot", "id": S1} in body["references"]


def test_report_evidence_lookup_denials(api):
    assert _invoke(api, "report_evidence_lookup", {"report_version_id": "missing"}).json()["status"] == "no_data"
    assert _invoke(api, "report_evidence_lookup", {"report_version_id": "version-org-b"}).json()["status"] == "not_authorized"


# --------------------------------------------------------------------------
# calculation_snapshot_lookup
# --------------------------------------------------------------------------
def test_calculation_snapshot_lookup_returns_ratified_provenance(api):
    body = _invoke(api, "calculation_snapshot_lookup", {"snapshot_id": S1}).json()
    assert body["status"] == "success"
    assert body["data"]["co2e_kg"] == "2469.16978"
    assert body["data"]["content_hash"] == "af640887"
    assert body["data"]["factor_kind"] == "emission_factor"
    assert body["data"]["source_item_id"] == "item-1"
    assert body["data"]["source_line_item_id"] == LINE1
    assert body["data"]["date"] == "2025-01-03"
    for forbidden in ("calculated_by", "performed_by", "request_id", "import_batch_id", "factor_set", "source_file", "source_page"):
        assert forbidden not in body["data"]
    assert {"kind": "calculation_snapshot", "id": S1} in body["references"]
    assert {"kind": "evidence_line_item", "id": LINE1} in body["references"]


def test_calculation_snapshot_lookup_denials(api):
    assert _invoke(api, "calculation_snapshot_lookup", {"snapshot_id": "missing"}).json()["status"] == "no_data"
    api.state["user"] = _user(BOB, ORG_B)
    body = _invoke(api, "calculation_snapshot_lookup", {"snapshot_id": S1}, org=ORG_B).json()
    assert body["status"] == "not_authorized" and body["data"] == {}


# --------------------------------------------------------------------------
# Input validation (PO §14)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("tool,payload,reason", [
    ("no_such_tool", {}, "unratified_tool"),
    ("report_lookup", {}, "missing_required_parameter"),
    ("report_lookup", {"report_id": R1, "extra": "x"}, "unknown_parameter"),
    ("report_lookup", {"report_id": "x" * 200}, "parameter_too_long"),
    ("report_evidence_lookup", {"report_version_id": None}, "missing_required_parameter"),
])
def test_invalid_inputs_are_refused(api, tool, payload, reason):
    body = _invoke(api, tool, payload).json()
    assert body["status"] == "invalid_input" and body["reason"] == reason


# --------------------------------------------------------------------------
# Deterministic intent classification (PO §12)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("show me the report for 2025", "report_lookup"),
    ("which version is current", "report_version_lookup"),
    ("show the evidence behind this number", "report_evidence_lookup"),
    ("what emission factor was used", "calculation_snapshot_lookup"),
])
def test_intent_routes_to_ratified_tools(api, text, expected):
    body = _intent(api, text).json()
    assert body["status"] == "success" and body["tool"] == expected


def test_intent_refuses_unsupported_and_ambiguous(api):
    assert _intent(api, "hello there").json()["reason"] == "unsupported_intent"
    ambiguous = _intent(api, "show me the evidence for version 2").json()
    assert ambiguous["status"] == "invalid_input"
    assert ambiguous["reason"] == "ambiguous_intent" and ambiguous["tool"] is None


# --------------------------------------------------------------------------
# Determinism and output bound (PO §13/§14)
# --------------------------------------------------------------------------
def test_identical_requests_produce_identical_results(api):
    first = _invoke(api, "report_lookup", {"report_id": R1}).json()
    second = _invoke(api, "report_lookup", {"report_id": R1}).json()
    assert first == second
    assert "timestamp" not in first and "produced_at" not in first


def test_output_is_bounded(api):
    for number in range(3, 260):
        api.world.versions.add({"id": f"v-{number}", "report_id": R1, "version_number": number,
                                "status": "DRAFT", "is_current": False,
                                "created_at": "2025-05-01T00:00:00"})
    body = _invoke(api, "report_lookup", {"report_id": R1}).json()
    assert body["truncated"] is True and len(body["data"]["versions"]) == 200


# --------------------------------------------------------------------------
# Persona matrix (PO §6) — ALLOW/DENY, revocation, gate refusals
# --------------------------------------------------------------------------
def test_every_authorized_persona_passes_and_unauthorized_personas_do_not(api):
    api.state["user"] = _user(BOB, ORG_A, role="org_member")
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "success"

    api.world.consultants.add_member(CONSULTANT)
    api.world.consultants.grant(ORG_A)
    api.state["user"] = _user(CONSULTANT, None, role="consultant", is_org_member=False)
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "success"
    api.world.consultants.grant(ORG_A, status="ended")
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "not_authorized"

    api.world.staff.add(STAFF, permissions={"can_view_all": True})
    api.state["user"] = _user(STAFF, None, role="admin", is_org_member=False, is_staff=True)
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "success"

    api.state["user"] = _user("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee", ORG_A, role="auditor")
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "not_authorized"


def test_staff_without_the_ops_permission_gains_no_tool_scope(api):
    api.world.staff.add(STAFF, permissions={"can_process": True})
    api.state["user"] = _user(STAFF, None, role="operator", is_org_member=False, is_staff=True)
    assert _invoke(api, "report_lookup", {"report_id": R1}).json()["status"] == "not_authorized"


def test_processing_entity_and_public_are_refused_at_the_gate(api):
    api.state["user"] = _user(STAFF, None, role="pe_manager", is_org_member=False, is_staff=True, entity_id="ent-1")
    assert _invoke(api, "report_lookup", {"report_id": R1}).status_code == 403
    api.state["unauthenticated"] = True
    assert _invoke(api, "report_lookup", {"report_id": R1}).status_code == 401
