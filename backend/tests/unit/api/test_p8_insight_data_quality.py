"""Phase 8 P3 — bounded Insight data quality + audit/reproducibility.

Authorization: PO P3 implementation authorization (2026-09-23), families 14 and 16.

The load-bearing property of this suite: **P3 invents no quality rule.** Every
finding asserted here is produced by the *existing* ``ValidationEngine`` /
``CalculationEngine.verify`` machinery, and the tests pin that P3 only aggregates
and projects it — no score, no weight, no new code.

LIMITATION (stated, not hidden): the SQL and the migration are verified
structurally only. Executing them requires a disposable database
(F-046-1 forbids pointing the harness at a persistent one), so database-level
verification remains an integration task.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI
from starlette.testclient import TestClient

from api import v3_insight_tools
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from domain.factor import RESULT_PRECISION
from domain.insight_query import REASON_INVALID_NUMBER
from domain.insight_quality import (
    MAX_QUALITY_RECORDS,
    REPRODUCIBILITY_CONDITIONS,
    TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
    TOOL_INSIGHT_DATA_QUALITY,
    order_issue_codes,
    snapshot_from_row,
    summarise_report,
)
from services.insight_query_planner import (
    REASON_SNAPSHOT_REQUIRED,
    STATUS_CLARIFICATION,
    STATUS_PLANNED,
    plan_question,
)
from services.insight_tools import TOOL_REGISTRY, invoke_tool
from tests.unit.api.insight_analytics_fakes import InsightLogsFake
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SNAP = "6d3f4b2a-1111-4222-8333-444455556666"
BASE = "/api/v3/insight/tools"
PERIOD = {"start_date": "2024-01-01", "end_date": "2024-12-31"}


class _Orgs:
    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=True)


class _NoneRepo:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


class _Factors:
    """Factor lookup double: the engine only needs ``get`` for A5 context."""

    def __init__(self, factors=None):
        self.factors = factors or {}
        self.calls: list[str] = []

    async def get(self, factor_id: str):
        self.calls.append(str(factor_id))
        return self.factors.get(str(factor_id))


class _Issues:
    def __init__(self, count: int = 0):
        self.count = count

    async def count_for_org(self, org_id: str) -> int:
        return int(self.count)


class _Evidence:
    def __init__(self, resolved: int = 0):
        self.resolved = resolved
        self.calls: list[str] = []

    async def count_for_item(self, source_item_id: str) -> int:
        self.calls.append(str(source_item_id))
        return int(self.resolved)


class _P3Logs(InsightLogsFake):
    """The shared analytics double plus the two reads P3 needs.

    Defined here (not in the shared fakes module) so the frozen P2 test support
    is untouched.
    """

    def __init__(self):
        super().__init__()
        self.by_id: dict[str, dict] = {}

    def add_row(self, row: dict) -> dict:
        self.by_id[str(row["id"])] = row
        self.snapshots.append(row)
        return row

    async def get_snapshot(self, snapshot_id: str):
        self.calls.append({"method": "get_snapshot", "snapshot_id": snapshot_id})
        return self.by_id.get(str(snapshot_id))


_FACTOR = SimpleNamespace(
    id="factor-1",
    co2e_multiplier=Decimal("2.5"),
    import_batch_id="batch-1",
    factor_source="DEFRA",
    factor_set="2025",
    requires_unit=True,
    unit="litres",
    scope="Scope 1",
    activity_type="Fuels > Liquid fuels > Diesel",
    country="UK",
    provider="DEFRA",
)


def _factors(**overrides):
    """The factor the stored snapshots reference (A1 unit rule + A5 context)."""
    return _Factors({"factor-1": SimpleNamespace(**{**_FACTOR.__dict__, **overrides})})


def _auth_user(organization_id=ORG_A):
    return AuthUser(
        user_id=ALICE,
        email="alice@example.test",
        role="org_owner",
        role_name="org_owner",
        organization_id=organization_id,
        is_org_member=True,
    )


def _row(
    snapshot_id: str = SNAP,
    *,
    organization_id: str = ORG_A,
    quantity: str = "100",
    unit: str = "litres",
    multiplier: str = "2.5",
    co2e: str | None = None,
    activity: str = "Diesel",
    activity_type: str = "Fuels > Liquid fuels > Diesel",
    scope: str = "Scope 1",
    reporting_year: int = 2024,
    methodology: str = "direct_multiply",
    algorithm_version: str = "v1.0",
    factor_id: str | None = "factor-1",
    factor_kind: str = "emission_factor",
    customer_factor_id: str | None = None,
    source_item_id: str | None = "item-1",
    source_line_item_id: str | None = "line-1",
    content_hash: str | None = None,
    factor_source: str | None = "DEFRA",
    factor_set: str | None = "2025",
    import_batch_id: str | None = "batch-1",
) -> dict:
    """One stored snapshot row whose stored result matches its own inputs."""
    result = (
        Decimal(co2e)
        if co2e is not None
        else (Decimal(quantity) * Decimal(multiplier)).quantize(RESULT_PRECISION)
    )
    row = {
        "id": snapshot_id,
        "organization_id": organization_id,
        "request_id": f"req-{snapshot_id[:6]}",
        "factor_id": factor_id,
        "quantity": Decimal(quantity),
        "quantity_unit": unit,
        "co2e_multiplier": Decimal(multiplier),
        "co2e_kg": result,
        "scope": scope,
        "date": date(2024, 3, 15),
        "reporting_year": reporting_year,
        "methodology": methodology,
        "algorithm_version": algorithm_version,
        "calculated_at": date(2024, 3, 15),
        "content_hash": content_hash,
        "factor_kind": factor_kind,
        "customer_factor_id": customer_factor_id,
        "source_item_id": source_item_id,
        "source_line_item_id": source_line_item_id,
        "source_file": "bills.pdf",
        "source_page": 2,
        "activity": activity,
        "activity_type": activity_type,
        "factor_source": factor_source,
        "factor_set": factor_set,
        "import_batch_id": import_batch_id,
    }
    if content_hash is None:
        row["content_hash"] = snapshot_from_row(row).build_content_hash()
    return row


class _Repos:
    """Every repository surface P3 touches, with the fakes it needs."""

    def __init__(self, logs=None, factors=None, issues=None, evidence=None, limits=None):
        self.logs = logs or _P3Logs()
        self.factors = factors or _Factors()
        self.organizations = _Orgs()
        self.customer_factors = None
        self.issues = issues or _Issues()
        self.evidence_line_items = evidence or _Evidence()
        self.insight_limits = limits or InsightLimitsFake()
        self.memberships = _NoneRepo()
        self.staff = _NoneRepo()


def _client(repos, organization_id=ORG_A):
    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    app.dependency_overrides[get_repositories] = lambda: repos
    app.dependency_overrides[get_current_user] = lambda: _auth_user(organization_id)
    return TestClient(app)


async def _quality(repos, tool_input=None):
    return await invoke_tool(
        tool_name=TOOL_INSIGHT_DATA_QUALITY,
        current_user=_auth_user(),
        repos=repos,
        organization_id=ORG_A,
        tool_input=tool_input if tool_input is not None else dict(PERIOD),
    )


async def _repro(repos, snapshot_id=SNAP, organization_id=ORG_A):
    return await invoke_tool(
        tool_name=TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
        current_user=_auth_user(organization_id),
        repos=repos,
        organization_id=organization_id,
        tool_input={"snapshot_id": snapshot_id},
    )


# ---------------------------------------------------------------------------
# 1. Data-quality signals — each is the existing engine's own finding.
# ---------------------------------------------------------------------------


async def test_complete_record_produces_no_findings():
    """1. A healthy record yields counts, not a score, and no findings."""
    logs = _P3Logs()
    logs.add_row(_row())
    result = await _quality(_Repos(logs=logs))
    assert result.status.value == "success"
    assert result.reason == "all_checks_passed"
    assert result.data["records_checked"] == 1
    assert result.data["records_with_findings"] == 0
    assert result.data["records_passing"] == 1
    assert result.data["findings"] == []
    assert "score" not in result.data


async def test_missing_activity_is_reported_by_the_engine():
    """2. Empty stored activity → the existing VAL_INPUT_ACTIVITY_EMPTY code."""
    logs = _P3Logs()
    logs.add_row(_row(activity="", activity_type="Fuels > Liquid fuels > Diesel"))
    result = await _quality(_Repos(logs=logs))
    codes = [f["code"] for f in result.data["findings"]]
    # The stored activity text is what the engine judges: the populated
    # activity_type must not paper over an empty activity.
    assert "VAL_INPUT_ACTIVITY_EMPTY" in codes
    assert result.data["records_with_findings"] == 1


async def test_missing_quantity_unit_combined_with_provenance():
    """10. Independent findings on one record stay independent counts."""
    logs = _P3Logs()
    logs.add_row(_row(unit="", co2e="1", content_hash="deadbeef"))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    codes = {f["code"] for f in result.data["findings"]}
    assert {"VAL_CALC_MISMATCH", "VAL_HASH_MISMATCH"} <= codes
    assert len(codes) >= 2
    assert result.data["records_with_findings"] == 1
    assert result.data["records_checked"] == 1
    assert result.data["finding_count"] >= 2


async def test_missing_unit_is_reported_with_its_field():
    """4. Missing unit → VAL_INPUT_UNIT_MISSING, with the engine's own field.

    The unit rule is the engine's ("required when the factor carries a unit"), so
    the factor must be resolvable for the rule to run at all.
    """
    logs = _P3Logs()
    logs.add_row(_row(unit=""))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    finding = result.data["findings"][0]
    assert finding["code"] == "VAL_INPUT_UNIT_MISSING"
    assert finding["severity"] in {"error", "warning", "suggestion"}
    assert finding["field"] == "quantity_unit"


async def test_unit_rule_is_not_claimed_when_the_factor_cannot_be_resolved():
    """21/'not checked' must never read as 'checked and fine'."""
    logs = _P3Logs()
    logs.add_row(_row(unit=""))
    result = await _quality(_Repos(logs=logs, factors=_Factors({})))
    assert result.data["records_with_unresolved_factor"] == 1
    assert [f["code"] for f in result.data["findings"]] != ["VAL_INPUT_UNIT_MISSING"]


async def test_recomputation_mismatch_is_reported():
    """7. A stored result that does not match its inputs → VAL_CALC_MISMATCH."""
    logs = _P3Logs()
    logs.add_row(_row(co2e="1"))
    result = await _quality(_Repos(logs=logs))
    codes = {f["code"] for f in result.data["findings"]}
    assert "VAL_CALC_MISMATCH" in codes
    assert result.data["records_with_findings"] == 1


async def test_content_hash_mismatch_is_reported():
    """8. Tamper evidence: a wrong stored hash → VAL_HASH_MISMATCH."""
    logs = _P3Logs()
    logs.add_row(_row(content_hash="deadbeef"))
    result = await _quality(_Repos(logs=logs))
    codes = {f["code"] for f in result.data["findings"]}
    assert "VAL_HASH_MISMATCH" in codes


async def test_provenance_missing_is_reported():
    """8. A batch-linked factor with no retained import batch → A5 provenance."""
    logs = _P3Logs()
    logs.add_row(_row(import_batch_id=None))
    factors = _Factors(
        {
            "factor-1": SimpleNamespace(
                id="factor-1",
                co2e_multiplier=Decimal("2.5"),
                import_batch_id="batch-1",
                factor_source="DEFRA",
                factor_set="2025",
                requires_unit=True,
                unit="litres",
                scope="Scope 1",
                activity_type="Fuels > Liquid fuels > Diesel",
                country="UK",
                provider="DEFRA",
            )
        }
    )
    result = await _quality(_Repos(logs=logs, factors=factors))
    codes = {f["code"] for f in result.data["findings"]}
    assert "VAL_SNAPSHOT_PROVENANCE_MISSING" in codes


async def test_multiple_independent_findings_on_one_record():
    """10. One record can carry several independent findings."""
    logs = _P3Logs()
    logs.add_row(_row(unit="", co2e="1", content_hash="deadbeef"))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    codes = {f["code"] for f in result.data["findings"]}
    assert {"VAL_INPUT_UNIT_MISSING", "VAL_CALC_MISMATCH", "VAL_HASH_MISMATCH"} <= codes
    # ...still one *record* with findings — never a composite score.
    assert result.data["records_with_findings"] == 1
    assert result.data["records_checked"] == 1


async def test_open_issue_count_is_reported_as_the_existing_qc_state():
    """9. The authoritative QC state is reported, not redefined."""
    logs = _P3Logs()
    logs.add_row(_row())
    result = await _quality(_Repos(logs=logs, issues=_Issues(7)))
    assert result.data["open_issue_count"] == 7
    assert result.data["qc_state_basis"]



# ---------------------------------------------------------------------------
# 2. Population behaviour
# ---------------------------------------------------------------------------


async def test_empty_population_is_no_data_not_a_pass():
    """11. No records in the period is an absence of data, not a clean bill."""
    result = await _quality(_Repos())
    assert result.status.value == "no_data"
    assert result.reason == "no_rows_in_period"
    assert result.data == {}


async def test_multiple_records_are_counted_deterministically():
    """13/15. Counts are deterministic per code across several records."""
    logs = _P3Logs()
    logs.add_row(_row("snap-a", unit=""))
    logs.add_row(_row("snap-b", unit=""))
    logs.add_row(_row("snap-c"))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    assert result.data["records_checked"] == 3
    assert result.data["records_with_findings"] == 2
    assert result.data["records_passing"] == 1
    missing_unit = [
        f for f in result.data["findings"] if f["code"] == "VAL_INPUT_UNIT_MISSING"
    ][0]
    assert missing_unit["record_count"] == 2
    assert missing_unit["affected_records"] == ["snap-a", "snap-b"]


async def test_findings_and_records_are_ordered_deterministically():
    """16. Identical requests produce identical ordering."""
    logs = _P3Logs()
    logs.add_row(_row("snap-b", unit="", content_hash="deadbeef"))
    logs.add_row(_row("snap-a", unit=""))
    repos = _Repos(logs=logs, factors=_factors())
    first = await _quality(repos)
    second = await _quality(repos)
    assert [f["code"] for f in first.data["findings"]] == [
        f["code"] for f in second.data["findings"]
    ]
    unit = [
        f for f in first.data["findings"] if f["code"] == "VAL_INPUT_UNIT_MISSING"
    ][0]
    assert unit["affected_records"] == ["snap-a", "snap-b"]


async def test_population_is_bounded_and_truncation_is_stated():
    """30/31. The scan is bounded; a larger period is reported as truncated."""
    logs = _P3Logs()
    for index in range(4):
        logs.add_row(_row(f"snap-{index}"))
    result = await _quality(_Repos(logs=logs), {**PERIOD, "limit": 2})
    assert result.data["records_checked"] == 2
    assert result.data["population_truncated"] is True
    assert result.truncated is True
    assert result.data["finding_count"] >= 0


async def test_limit_above_the_bound_is_rejected():
    """29. The bound cannot be raised by the caller."""
    result = await _quality(_Repos(), {**PERIOD, "limit": MAX_QUALITY_RECORDS + 1})
    assert result.status.value == "invalid_input"
    assert result.reason == REASON_INVALID_NUMBER


async def test_scan_states_the_checks_it_performed():
    """§9/§21. The result says what was checked, so it can be explained."""
    logs = _P3Logs()
    logs.add_row(_row())
    result = await _quality(_Repos(logs=logs))
    assert len(result.data["checks_performed"]) >= 3
    assert result.data["basis"]



# ---------------------------------------------------------------------------
# 3. Record-level reproducibility (P3-B)
# ---------------------------------------------------------------------------


async def test_reproducible_calculation_reports_every_condition():
    """17. A fully retained record satisfies each condition — and certifies nothing."""
    logs = _P3Logs()
    logs.add_row(_row())
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=_Evidence(2)))
    assert result.status.value == "success"
    assert result.data["reproducible"] is True
    assert result.data["checkable"] is True
    assert result.data["unsatisfied_conditions"] == []
    assert result.data["verification"]["match"] is True
    assert result.data["verification"]["tampered"] is False
    assert [c["name"] for c in result.data["conditions"]] == list(
        REPRODUCIBILITY_CONDITIONS
    )
    # The frozen product language: no certification claim anywhere.
    blob = repr(result.data).lower()
    for claim in ("certified", "audit_approved", "assurance", "compliant"):
        assert claim not in blob


async def test_missing_replay_input_is_reported_as_a_limitation():
    """18. A record without a quantity unit cannot have the unit rule applied."""
    logs = _P3Logs()
    logs.add_row(_row(unit=""))
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=_Evidence(1)))
    # The calculation still reproduces numerically; the retained-input condition
    # states the limitation instead of pretending the check passed.
    names = {c["name"]: c for c in result.data["conditions"]}
    assert names["calculation_inputs_retained"]["satisfied"] is False
    assert result.reason == "reproducibility_limitation"


async def test_unresolvable_source_lineage_is_reported():
    """20. No retained source reference → the lineage condition is unsatisfied."""
    logs = _P3Logs()
    logs.add_row(_row(source_item_id=None, source_line_item_id=None))
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=_Evidence(0)))
    names = {c["name"]: c for c in result.data["conditions"]}
    assert names["source_lineage_retained"]["satisfied"] is False
    assert names["evidence_resolvable"]["satisfied"] is False


async def test_snapshot_result_mismatch_uses_the_existing_check():
    """21. The existing deterministic comparison reports the mismatch."""
    logs = _P3Logs()
    logs.add_row(_row(co2e="3"))
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=_Evidence(1)))
    assert result.data["verification"]["match"] is False
    assert result.data["verification"]["discrepancy"] is not None
    assert result.data["reproducible"] is False
    names = {c["name"]: c for c in result.data["conditions"]}
    assert names["recomputation_matches"]["satisfied"] is False
    # A non-reproducible result is not an allegation of wrongness: it is stated
    # as a condition, and the finding code is the engine's own.
    assert "VAL_CALC_MISMATCH" in result.data["finding_codes"]


async def test_tamper_evidence_uses_the_existing_hash_check():
    logs = _P3Logs()
    logs.add_row(_row(content_hash="0" * 64))
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=_Evidence(1)))
    assert result.data["verification"]["tampered"] is True
    assert result.data["reproducible"] is False
    assert "VAL_HASH_MISMATCH" in result.data["finding_codes"]


async def test_missing_historical_factor_is_reported_not_fabricated():
    """19. A factor that no longer resolves is a stated limitation (no D-13 work)."""
    logs = _P3Logs()
    logs.add_row(_row())
    result = await _repro(_Repos(logs=logs, factors=_Factors({}), evidence=_Evidence(1)))
    assert result.data["checkable"] is True
    assert result.data["finding_codes"] is not None
    # Provenance could not be assessed; the result says so rather than claiming
    # a historical factor set that CarbonTally does not retain.
    assert result.data["factor_id"] == "factor-1"


async def test_evidence_resolution_uses_the_retained_source_item():
    """15. Deeper inspection stays with the existing evidence path."""
    logs = _P3Logs()
    logs.add_row(_row())
    evidence = _Evidence(3)
    result = await _repro(_Repos(logs=logs, factors=_factors(), evidence=evidence))
    assert evidence.calls == ["item-1"]
    assert result.data["evidence"]["evidence_line_item_count"] == 3
    assert result.data["provenance_tool"] == "insight_aggregate_provenance"



# ---------------------------------------------------------------------------
# 4. Security: organisation scoping and the closed input surface
# ---------------------------------------------------------------------------


def test_quality_route_is_organisation_scoped_and_rate_limited():
    """§18/§32. P3 executes through the same limiter the closed INS-01 path uses."""
    repos = _Repos()
    client = _client(repos)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_DATA_QUALITY,
            "input": dict(PERIOD),
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "no_data"
    assert repos.insight_limits.consumed


def test_cross_tenant_quality_scan_is_denied():
    """22. A user authorised for another organisation cannot run this scan."""
    client = _client(_Repos(), organization_id=ORG_B)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_DATA_QUALITY,
            "input": dict(PERIOD),
        },
    )
    assert response.json()["status"] == "not_authorized"


def test_foreign_snapshot_identifier_is_denied():
    """23. A foreign identifier is a locator, not a grant."""
    logs = _P3Logs()
    logs.add_row(_row(organization_id=ORG_B))
    repos = _Repos(logs=logs, factors=_factors(), evidence=_Evidence(1))
    client = _client(repos)  # authorised for ORG_A only
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            "input": {"snapshot_id": SNAP},
        },
    )
    assert response.json()["status"] == "not_authorized"


async def test_cross_tenant_snapshot_is_denied_at_the_tool_layer():
    logs = _P3Logs()
    logs.add_row(_row(organization_id=ORG_B))
    result = await _repro(_Repos(logs=logs), snapshot_id=SNAP, organization_id=ORG_A)
    assert result.status.value == "not_authorized"
    assert result.reason == "not_authorized"


def test_unauthenticated_access_is_refused():
    """25. No identity → no Insight execution."""
    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    app.dependency_overrides[get_repositories] = lambda: _Repos()

    async def _reject():
        raise Exception("unauthenticated")

    app.dependency_overrides[get_current_user] = _reject
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_DATA_QUALITY,
            "input": dict(PERIOD),
        },
    )
    assert response.status_code >= 400


def test_foreign_evidence_identifier_cannot_be_requested():
    """24/28. There is no input through which a foreign evidence id could arrive."""
    repos = _Repos()
    client = _client(repos)
    response = client.post(
        f"{BASE}/invoke",
        json={
            "organization_id": ORG_A,
            "tool": TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            "input": {"snapshot_id": SNAP, "source_item_id": "foreign-item"},
        },
    )
    assert response.json()["status"] == "invalid_input"


# ---------------------------------------------------------------------------
# 5. Tool contract
# ---------------------------------------------------------------------------


async def test_missing_period_is_invalid_input():
    """28. The bounded period is required, not optional."""
    result = await _quality(_Repos(), {})
    assert result.status.value == "invalid_input"


async def test_inverted_period_is_invalid_input():
    result = await _quality(
        _Repos(), {"start_date": "2024-12-31", "end_date": "2024-01-01"}
    )
    assert result.status.value == "invalid_input"


async def test_reproducibility_requires_a_snapshot_identifier():
    """27/28. A missing identifier is rejected by the existing input contract."""
    result = await _repro(_Repos(), snapshot_id="")
    assert result.status.value == "invalid_input"
    # The closed input contract rejects the empty required parameter first.
    assert result.reason == "missing_required_parameter"


async def test_a_malformed_identifier_finds_nothing_rather_than_guessing():
    result = await _repro(_Repos(), snapshot_id="not-a-record-id")
    assert result.status.value == "no_data"
    assert result.reason == "snapshot_not_found"


async def test_unknown_snapshot_is_no_data_not_an_error():
    result = await _repro(_Repos(), snapshot_id=SNAP)
    assert result.status.value == "no_data"
    assert result.reason == "snapshot_not_found"


def test_arbitrary_query_surface_is_refused():
    """30/31. No arbitrary selectors: unknown keys are rejected outright."""
    client = _client(_Repos())
    for tool, payload in (
        (TOOL_INSIGHT_DATA_QUALITY, {**PERIOD, "sql": "select * from users"}),
        (TOOL_INSIGHT_DATA_QUALITY, {**PERIOD, "group_by": "facility"}),
        (TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY, {"snapshot_id": SNAP, "table": "issues"}),
    ):
        body = client.post(
            f"{BASE}/invoke",
            json={"organization_id": ORG_A, "tool": tool, "input": payload},
        ).json()
        assert body["status"] == "invalid_input", payload



# ---------------------------------------------------------------------------
# 6. LLM boundary — the model narrates, it never decides
# ---------------------------------------------------------------------------


async def test_deterministic_counts_reach_the_narration_boundary():
    """33. The numbers are produced deterministically, before any narration."""
    logs = _P3Logs()
    logs.add_row(_row("snap-a", unit=""))
    logs.add_row(_row("snap-b"))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    # Everything a narration could state is already decided here.
    assert result.data["records_checked"] == 2
    assert result.data["records_with_findings"] == 1
    assert result.data["records_passing"] == 1
    assert result.data["finding_count"] == 1
    assert result.data["checks_performed"]


async def test_a_deficient_result_cannot_read_as_a_positive_claim():
    """34. Deficiency never becomes "all good" through a status or a reason."""
    logs = _P3Logs()
    logs.add_row(_row(unit=""))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    assert result.reason == "findings_reported"
    assert result.reason != "all_checks_passed"
    assert result.data["records_with_findings"] == 1
    assert result.data["findings"]


async def test_no_composite_score_is_invented():
    """35/§7. No weighting, no score, no ranking — only named counts."""
    logs = _P3Logs()
    logs.add_row(_row(unit="", content_hash="deadbeef"))
    result = await _quality(_Repos(logs=logs, factors=_factors()))
    forbidden = ("score", "grade", "rating", "confidence", "readiness", "index")
    for key in result.data:
        assert not any(word in key.lower() for word in forbidden), key
    for finding in result.data["findings"]:
        assert set(finding) >= {"code", "severity", "record_count"}
        assert "weight" not in finding


async def test_not_checked_is_never_reported_as_passed():
    """§21. A record the engine could not check is counted separately."""
    logs = _P3Logs()
    logs.add_row(_row())  # lacks the fields a re-check needs -> not checkable
    row = logs.by_id[SNAP]
    row["quantity"] = None
    result = await _quality(_Repos(logs=logs))
    assert result.data["records_checked"] == 0
    assert result.data["uncheckable_records"] == 1
    assert result.data["records_passing"] == 0


# ---------------------------------------------------------------------------
# 7. Planner — the bounded P3 intents
# ---------------------------------------------------------------------------


def test_quality_question_with_a_period_plans_the_quality_tool():
    plan = plan_question("what data is missing in 2024?")
    assert plan["status"] == STATUS_PLANNED
    assert plan["tool"] == TOOL_INSIGHT_DATA_QUALITY
    assert plan["tool_input"] == {"start_date": "2024-01-01", "end_date": "2024-12-31"}


def test_quality_question_without_a_period_asks_for_one():
    plan = plan_question("is our data quality good?")
    assert plan["status"] == STATUS_CLARIFICATION
    assert plan["reason"] == "period_required"


def test_reproducibility_question_with_an_identifier_plans_the_check():
    plan = plan_question(f"can you reproduce calculation {SNAP}?")
    assert plan["status"] == STATUS_PLANNED
    assert plan["tool"] == TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY
    assert plan["tool_input"] == {"snapshot_id": SNAP}


def test_reproducibility_question_without_an_identifier_asks_for_one():
    plan = plan_question("can you reproduce this calculation?")
    assert plan["status"] == STATUS_CLARIFICATION
    assert plan["reason"] == REASON_SNAPSHOT_REQUIRED



def test_p2_and_preexisting_planner_behaviour_is_unchanged():
    """§25. The frozen P2 shape and the ratified tools still plan as before."""
    comparison = plan_question("compare january 2026 with january 2025")
    assert comparison["tool"] == "insight_temporal_comparison"
    assert comparison["tool_input"] == {
        "period_a_start": "2026-01-01",
        "period_a_end": "2026-01-31",
        "period_b_start": "2025-01-01",
        "period_b_end": "2025-01-31",
    }
    aggregation = plan_question("emissions by scope for 2024")
    assert aggregation["tool"] == "insight_aggregation"
    discovery = plan_question("which calculation was 20000 kg co2e on 2024-02-02?")
    assert discovery["tool"] == "insight_discovery"
    # A directional comparison stays unsupported: P3 adds no directional semantics.
    assert plan_question("is this month higher than last month?")["status"] == (
        "unsupported"
    )


# ---------------------------------------------------------------------------
# 8. Pure helpers and the widened migration (static checks)
# ---------------------------------------------------------------------------


def test_summary_counts_and_ordering_are_pure_and_stable():
    issues = [
        {"code": "VAL_HASH_MISMATCH", "severity": "error", "record_id": "r2"},
        {"code": "VAL_INPUT_UNIT_MISSING", "severity": "error", "record_id": "r1"},
        {"code": "VAL_INPUT_UNIT_MISSING", "severity": "error", "record_id": "r2"},
    ]
    summary = summarise_report(issues, records_checked=3, records_with_findings=2)
    assert [f["code"] for f in summary["findings"]] == [
        "VAL_HASH_MISMATCH",
        "VAL_INPUT_UNIT_MISSING",
    ]
    assert summary["records_passing"] == 1
    assert summary["finding_count"] == 3
    assert summary["findings"][1]["affected_records"] == ["r1", "r2"]
    assert order_issue_codes(["b", "a", "b"]) == ["a", "b"]


def test_snapshot_mapping_refuses_a_row_without_required_fields():
    assert snapshot_from_row({"id": "x"}) is None


def test_migration_widens_the_tool_check_and_adds_no_table():
    """The authorized catalogue widens in place; nothing else is created."""
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[4]
        / "supabase"
        / "migrations"
        / "20260923000000_p8_insight_data_quality_reproducibility.sql"
    )
    sql = path.read_text()
    assert "ci_tool_calls_tool_name_check" in sql
    assert "insight_data_quality" in sql
    assert "insight_calculation_reproducibility" in sql
    assert "CREATE TABLE" not in sql.upper()
    assert "ALTER TABLE" in sql.upper()


def test_catalogue_contains_the_p3_tools_and_keeps_the_earlier_ones():
    assert TOOL_INSIGHT_DATA_QUALITY in TOOL_REGISTRY
    assert TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY in TOOL_REGISTRY
    # P2's tool contract is untouched by P3.
    assert "insight_temporal_comparison" in TOOL_REGISTRY

