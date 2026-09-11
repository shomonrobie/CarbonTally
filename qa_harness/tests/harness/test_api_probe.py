"""API probe engine self-tests — no live stack (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from qa_harness.api import probe as probe_module
from qa_harness.api.probe import (
    ApiProbeEngine,
    ProbeSpec,
    _classify,
    build_probe_specs,
    build_smoke_probes,
)
from qa_harness.api.session import ApiSessionPool
from qa_harness.core.config import TargetEnv
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.run_context import RunContext
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore
from qa_harness.identities.loader import Identity, generate_full_population
from qa_harness.identities.resolver import IdentityResolver

ENV = TargetEnv(
    name="local",
    api_url="http://localhost:8050",
    supabase_auth_url="http://127.0.0.1:54425",
)


class FakeResponse:
    def __init__(self, status: int, text: str = "") -> None:
        self.status_code = status
        self.text = text


class FakePool(ApiSessionPool):
    """Session pool that never contacts GoTrue."""

    def __init__(self) -> None:
        super().__init__(env=ENV, password="unused")

    def session(self, identity: Identity) -> Any:
        return None  # not needed; headers() is overridden

    def headers(self, identity: Identity) -> Dict[str, str]:
        return {"Authorization": "Bearer test-token"}


def _ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RunContext:
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "demo-pass-2026!")
    return RunContext(
        env=ENV, env_name="local", git_sha="abc1234",
        store=FindingStore(tmp_path / "findings"),
        evidence=EvidenceStore(tmp_path / "evidence"),
        registry=EvidenceRegistry(EvidenceStore(tmp_path / "evidence2")),
    )


def _resolver() -> IdentityResolver:
    population = {i.email: i for i in generate_full_population()}
    return IdentityResolver(population=population)


def test_classify_table() -> None:
    assert _classify("DENY", 403) == "PASS"
    assert _classify("DENY", 404) == "PASS"
    assert _classify("DENY", 200) == "FAIL"
    assert _classify("DENY", 422) == "WARNING"
    assert _classify("ALLOW", 201) == "PASS"
    assert _classify("ALLOW", 401) == "FAIL"
    assert _classify("ALLOW", 404) == "WARNING"
    assert _classify("NO_PATH", 404) == "PASS"
    assert _classify("NO_PATH", 200) == "FAIL"
    assert _classify("HTTP 200", 200) == "PASS"
    assert _classify("HTTP 200", 500) == "FAIL"


def test_probe_spec_sets_cover_matrix_and_security() -> None:
    specs = build_probe_specs()
    ids = [s.id for s in specs]
    # every documented matrix + security boundary id must be bound
    from qa_harness.api.authorization import AuthorizationMatrix
    from qa_harness.api.security import ApiSecurityAudit
    matrix_ids = {e.id for e in AuthorizationMatrix().expectations}
    boundary_ids = {b.id for b in ApiSecurityAudit().boundaries}
    missing_matrix = matrix_ids - set(ids)
    missing_boundaries = boundary_ids - set(ids)
    assert not missing_matrix, f"unbound matrix expectations: {sorted(missing_matrix)}"
    assert not missing_boundaries, f"unbound security boundaries: {sorted(missing_boundaries)}"
    assert any(s.mutation == "upload" for s in specs)
    assert sum(1 for s in specs if s.kind == "security") >= 10


def test_smoke_probes_are_read_only() -> None:
    for spec in build_smoke_probes():
        assert spec.mutation == "none"
        assert spec.method == "GET"


def test_upload_probes_skipped_in_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool(),
                            allow_upload_probes=False, allow_empty_body_mutation=True)
    spec = ProbeSpec("UPLOAD-X", "authz", "POST", "/api/v3/uploads", "customer_viewer",
                     "DENY", mutation="upload")
    result = engine._execute(spec, workflow="customer", source="test")
    assert result.outcome == "SKIPPED"
    assert "READ-ONLY" in result.error


def test_deny_probe_passes_on_403(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("T1", "authz", "GET", "/api/v3/documents?organization_id={org_b}",
                     "customer_owner", "DENY")
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: FakeResponse(403)  # type: ignore[assignment]
    try:
        result = engine._execute(spec, workflow="customer", source="test")
    finally:
        probe_module.requests.request = real_request
    assert result.outcome == "PASS"
    assert result.actual_status == 403


def test_deny_probe_fails_on_200(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("T2", "authz", "GET", "/api/v3/documents?organization_id={org_b}",
                     "customer_owner", "DENY", severity="P0")
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: FakeResponse(200, "leaked docs")  # type: ignore[assignment]
    try:
        results = engine.run([spec], source="test")
    finally:
        probe_module.requests.request = real_request
    assert results[0].outcome == "FAIL"
    # a finding must be emitted with evidence
    assert len(engine.findings) == 1
    assert engine.findings[0].severity == "P0"
    assert engine.findings[0].id.startswith("QA-API-")
    assert engine.findings[0].evidence, "evidence must be attached on failure"


def test_json_mutation_gate_passing_is_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("T3", "authz", "POST", "/api/v3/processing/items/{item_id}/customer-review",
                     "customer_member", "DENY", mutation="json", body={"approved": True})
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: FakeResponse(422)  # type: ignore[assignment]
    try:
        result = engine._execute(spec, workflow="customer", source="test")
    finally:
        probe_module.requests.request = real_request
    assert result.outcome == "WARNING"


def test_po_decision_required_not_a_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("AUTHZ-26", "authz", "POST", "/api/v3/customer-factors/{item_id}/approve",
                     "customer_owner", "PO DECISION REQUIRED", mutation="json", body={})
    result = engine._execute(spec, workflow="customer", source="test")
    assert result.outcome == "PO DECISION REQUIRED"
    assert engine._finding_for(result, workflow="customer", source="test") is None


def test_engine_run_emits_and_summarizes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    specs = [
        ProbeSpec("S1", "authz", "GET", "/api/v3/documents?organization_id={org_b}",
                  "customer_owner", "DENY"),
        ProbeSpec("S2", "endpoint", "GET", "/api/v3/ops/me", "customer_owner", "HTTP 200"),
    ]
    responses = iter([FakeResponse(403), FakeResponse(200, '{"me":{}}')])
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: next(responses)  # type: ignore[assignment]
    try:
        engine.run(specs, source="test")
    finally:
        probe_module.requests.request = real_request
    summary = engine.summary()
    assert summary.get("PASS") == 2
    assert engine.findings == []


# --- V1.2 calibration: classification semantics ----------------------------


def test_warning_finding_classified_inconclusive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from qa_harness.core.findings import FindingClassification

    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("T4", "authz", "POST", "/api/v3/processing/items/{item_id}/customer-review",
                     "customer_member", "DENY", mutation="json", body={"approved": True})
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: FakeResponse(422, "validation error")  # type: ignore[assignment]
    try:
        result = engine._execute(spec, workflow="customer", source="test")
    finally:
        probe_module.requests.request = real_request
    finding = engine._finding_for(result, workflow="customer", source="test")
    assert finding is not None
    assert finding.classification == FindingClassification.INCONCLUSIVE
    assert "inconclusive" in finding.title.lower()
    assert finding.severity == "P3"


def test_fail_finding_classified_real(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from qa_harness.core.findings import FindingClassification

    ctx = _ctx(tmp_path, monkeypatch)
    engine = ApiProbeEngine(ctx, _resolver(), FakePool())
    spec = ProbeSpec("T5", "authz", "GET", "/api/v3/documents?organization_id={org_b}",
                     "customer_owner", "DENY", severity="P0")
    real_request = probe_module.requests.request
    probe_module.requests.request = lambda *a, **k: FakeResponse(200, "leaked docs")  # type: ignore[assignment]
    try:
        result = engine._execute(spec, workflow="customer", source="test")
    finally:
        probe_module.requests.request = real_request
    finding = engine._finding_for(result, workflow="customer", source="test")
    assert finding is not None
    assert finding.classification == FindingClassification.REAL


def test_smoke_probes_supply_required_params() -> None:
    """SMOKE probes must supply every required query param so a non-2xx is a
    real app signal, not a 422 validation defect of the harness (V1.2)."""
    required_by_path = {
        "/api/v3/emissions/dashboard": {"organization_id", "start_date", "end_date"},
        "/api/v3/processing/queue": {"organization_id", "stage"},
        "/api/v3/processing/customer-review": {"organization_id"},
        "/api/v3/messaging/conversations": {"organization_id"},
        "/api/v3/reports": {"organization_id"},
        "/api/v3/customer-factors": {"organization_id"},
        "/api/v3/documents": {"organization_id"},
        "/api/v3/search": {"organization_id"},
        "/api/v3/processing/status": {"organization_id"},
        "/api/v3/processing/dashboard": {"organization_id"},
    }
    for spec in build_smoke_probes():
        path = spec.endpoint.split("?")[0]
        required = required_by_path.get(path, set())
        query = spec.endpoint.split("?", 1)[1] if "?" in spec.endpoint else ""
        for param in required:
            assert f"{param}=" in query, (
                f"{spec.id} must include required param {param}"
            )
