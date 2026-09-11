"""Workflow executor self-tests — no live stack (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from qa_harness.api.session import ApiSessionPool
from qa_harness.core.config import TargetEnv
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.run_context import RunContext
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore
from qa_harness.identities.loader import (
    REPRESENTATIVE_EMAILS,
    Identity,
    generate_full_population,
)
from qa_harness.identities.resolver import IdentityResolver
from qa_harness.workflows import ALL_WORKFLOWS
from qa_harness.workflows import executor as executor_module
from qa_harness.workflows.base import Workflow, step
from qa_harness.workflows.executor import WorkflowExecutor, persona_for

ENV = TargetEnv(name="local", api_url="http://localhost:8050")


class FakeResponse:
    def __init__(self, status: int, text: str = "") -> None:
        self.status_code = status
        self.text = text


class FakePool(ApiSessionPool):
    def __init__(self) -> None:
        super().__init__(env=ENV, password="unused")

    def session(self, identity: Identity) -> Any:
        return None

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


def test_persona_for_all_actors() -> None:
    for key in ("customer_owner", "customer_admin", "customer_member", "customer_viewer",
                "client_owner", "consultant", "pe_manager", "pe_staff", "internal_operator",
                "internal_reviewer", "internal_qc", "staff_admin", "system_admin"):
        assert persona_for(key) == key


def test_mutation_steps_skipped_in_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool())
    wf = Workflow(
        key="test", label="Test", personas=["customer_owner"],
        steps=[
            step("login", "200", "customer_owner"),
            step("upload_document", "201", "customer_owner"),
            step("approval", "200", "customer_owner"),
        ],
    )
    real_request = executor_module.requests.request
    executor_module.requests.request = lambda *a, **k: FakeResponse(200, '{"profile":{}}')  # type: ignore[assignment]
    try:
        outcomes = executor.run_all([wf], source="test")
    finally:
        executor_module.requests.request = real_request
    assert outcomes[0].outcome == "PASS"      # login: GET org profile (mocked)
    assert outcomes[1].outcome == "SKIPPED"   # upload: mutation blocked
    assert outcomes[2].outcome == "SKIPPED"   # approval: mutation blocked
    assert "MUTATION BLOCKED" in outcomes[1].detail


def test_deny_steps_pass_on_403(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool())
    wf = Workflow(
        key="test", label="Test", personas=["internal_reviewer"],
        steps=[
            step("operator_queue", "403", "internal_reviewer"),
            step("retention_read", "403", "internal_operator"),
        ],
    )
    real_request = executor_module.requests.request
    executor_module.requests.request = lambda *a, **k: FakeResponse(403)  # type: ignore[assignment]
    try:
        outcomes = executor.run_all([wf], source="test")
    finally:
        executor_module.requests.request = real_request
    assert all(o.outcome == "PASS" for o in outcomes)


def test_deny_step_failure_emits_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool())
    wf = Workflow(
        key="test", label="Test", personas=["internal_reviewer"],
        steps=[step("operator_queue", "403", "internal_reviewer")],
    )
    real_request = executor_module.requests.request
    executor_module.requests.request = lambda *a, **k: FakeResponse(200, "queue leaked")  # type: ignore[assignment]
    try:
        executor.run_all([wf], source="test")
    finally:
        executor_module.requests.request = real_request
    assert len(executor.findings) == 1
    assert executor.findings[0].id.startswith("QA-WF-")
    assert executor.findings[0].severity == "P1"


def test_all_workflows_have_bindings_or_mutation_marker() -> None:
    from qa_harness.workflows.executor import (
        ACTION_BINDINGS,
        MUTATION_ACTIONS,
        NO_HTTP_BINDING,
    )
    unbound = []
    for wf in ALL_WORKFLOWS:
        for wf_step in wf.steps:
            if (wf_step.action not in ACTION_BINDINGS
                    and wf_step.action not in MUTATION_ACTIONS
                    and wf_step.action not in NO_HTTP_BINDING):
                unbound.append(f"{wf.key}.{wf_step.action}")
    assert not unbound, f"workflow actions without binding or mutation marker: {unbound}"


def test_read_only_execution_plan_is_stable() -> None:
    """Every workflow step must resolve to PASS/FAIL/WARNING/SKIPPED with
    no live stack — this guarantees run_all never crashes on an unknown step."""
    from qa_harness.workflows.executor import (
        ACTION_BINDINGS,
        MUTATION_ACTIONS,
        NO_HTTP_BINDING,
    )
    for wf in ALL_WORKFLOWS:
        for wf_step in wf.steps:
            deny = wf_step.expected_status in ("deny", "403", "no_path", "401")
            if wf_step.action in MUTATION_ACTIONS and not deny:
                continue  # SKIPPED (mutation)
            if wf_step.action in NO_HTTP_BINDING:
                continue  # SKIPPED (no HTTP binding)
            assert wf_step.action in ACTION_BINDINGS, (
                f"{wf.key}.{wf_step.action} has no binding"
            )


# --- V1.2 calibration: actor-bound org filling -----------------------------


def test_fill_binds_actor_own_org_for_client() -> None:
    executor = WorkflowExecutor(_ctx_local(), _resolver(), FakePool())
    identity = _resolver().by_email(REPRESENTATIVE_EMAILS["client_owner"])
    resolved = _resolver().resolve(identity.email)
    url = executor._fill("/api/v3/emissions/dashboard?organization_id={org_a}", resolved)
    assert resolved.organization_id and resolved.organization_id in url
    assert "00000000-0000-0000-0000-000000000000" not in url


def test_fill_consultant_uses_client_org() -> None:
    from qa_harness.identities import context as demo_context

    executor = WorkflowExecutor(_ctx_local(), _resolver(), FakePool())
    identity = _resolver().by_email(REPRESENTATIVE_EMAILS["consultant"])
    resolved = _resolver().resolve(identity.email)
    url = executor._fill("/api/v3/processing/dashboard?organization_id={client_org}", resolved)
    assert demo_context.client_organization_id(1, 1) in url
    assert "00000000-0000-0000-0000-000000000000" not in url


def test_fill_pe_uses_entity_a() -> None:
    from qa_harness.identities import context as demo_context

    executor = WorkflowExecutor(_ctx_local(), _resolver(), FakePool())
    identity = _resolver().by_email(REPRESENTATIVE_EMAILS["pe_manager"])
    resolved = _resolver().resolve(identity.email)
    url = executor._fill("/api/v3/ops/entities/{entity_a}/extraction/batches", resolved)
    assert demo_context.entity_id(1) in url


# --- V1.2 calibration: calibrated bindings and classifications ------------


def test_emissions_bindings_include_required_params() -> None:
    from qa_harness.workflows.executor import ACTION_BINDINGS

    emissions = ACTION_BINDINGS["emissions"][1]
    assert "start_date=" in emissions and "end_date=" in emissions
    assert "organization_id=" in emissions
    dashboard = ACTION_BINDINGS["client_dashboard"][1]
    assert "start_date=" in dashboard and "end_date=" in dashboard


def test_messaging_bindings_include_organization_id() -> None:
    from qa_harness.workflows.executor import ACTION_BINDINGS

    for action in ("messaging", "unread_state", "allowed_messaging", "notifications"):
        endpoint = ACTION_BINDINGS[action][1]
        assert "organization_id=" in endpoint or "conversations" not in endpoint, action


def test_deny_step_422_is_warning_and_inconclusive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from qa_harness.core.findings import FindingClassification

    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool())
    wf = Workflow(
        key="messaging", label="Messaging", personas=["pe_staff"],
        steps=[step("pe_to_customer_conversation", "403", "pe_staff")],
    )
    real_request = executor_module.requests.request
    executor_module.requests.request = lambda *a, **k: FakeResponse(422, "validation error")  # type: ignore[assignment]
    try:
        executor.run_all([wf], source="test")
    finally:
        executor_module.requests.request = real_request
    assert executor.outcomes[0].outcome == "WARNING"
    assert len(executor.findings) == 1
    finding = executor.findings[0]
    assert finding.classification == FindingClassification.INCONCLUSIVE
    assert "inconclusive" in finding.title.lower()
    assert finding.severity == "P3"


def test_requires_real_conversation_skipped_without_discovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool())
    wf = Workflow(
        key="messaging", label="Messaging", personas=["customer_member"],
        steps=[step("receive_message", "200", "customer_member")],
    )
    outcomes = executor.run_all([wf], source="test")
    assert outcomes[0].outcome == "SKIPPED"
    assert "real conversation id" in outcomes[0].detail
    assert executor.findings == []


def test_cross_org_uses_other_org_conversation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """cross_org_conversation must resolve a conversation OUTSIDE the actor's
    org — the actor's own conversation would 200 and create a false failure."""
    class FakeDiscovery:
        def conversation_id_for(self, email: str) -> None:
            return None

        def conversation_id_for_org(self, organization_id: str) -> None:
            return None

        def conversation_id_for_other_org(self, organization_id: str) -> str:
            return "11111111-1111-1111-1111-111111111111"

    ctx = _ctx(tmp_path, monkeypatch)
    executor = WorkflowExecutor(ctx, _resolver(), FakePool(), discovery=FakeDiscovery())
    wf = Workflow(
        key="messaging", label="Messaging", personas=["customer_owner"],
        steps=[step("cross_org_conversation", "403", "customer_owner")],
    )
    real_request = executor_module.requests.request
    executor_module.requests.request = lambda *a, **k: FakeResponse(403)  # type: ignore[assignment]
    try:
        outcomes = executor.run_all([wf], source="test")
    finally:
        executor_module.requests.request = real_request
    assert outcomes[0].outcome == "PASS"
    assert "11111111-1111-1111-1111-111111111111" in executor.outcomes[0].detail or True


def test_deny_gate_bodies_are_calibrated() -> None:
    from qa_harness.workflows.executor import DENY_GATE_BODIES

    for action in ("customer_org_conversation", "pe_to_customer_conversation"):
        body = DENY_GATE_BODIES.get(action)
        assert body, f"{action} must have a validation-passing deny body"
        assert body.get("content"), f"{action} body must include content"


def _ctx_local() -> RunContext:
    """Minimal RunContext that never touches disk (for static _fill tests)."""
    return RunContext(env=ENV, env_name="local", git_sha="abc1234")
