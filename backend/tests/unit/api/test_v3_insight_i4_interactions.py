"""I4 — Layer-2 interaction orchestration (persistence, authz, provider, audit).

Authorization: PO I4 Implementation Authorization (2026-09-21) / PO Q1–Q14.
The I3 tool layer is stubbed where a specific tool outcome is under test, so these
tests pin the *I4* contract (lifecycle, answer states, append-only evidence,
idempotency, truthful provider behaviour, audit correlation, creator privacy)
independently of the closed I3 six-point contract.
"""
from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from api import v3_insight_interactions as api_mod
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from domain.insight_interaction import (
    ALLOWED_TOOL_STATUSES,
    AnswerStatus,
    InsightInteraction,
    InsightToolCall,
    INTERACTION_CONTRACT_VERSION,
)
from domain.insight_tool import InsightReference, ToolResult, ToolStatus
from services import insight_interactions as svc
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
C1 = "cccccccc-1111-4111-8111-111111111111"
R1 = "11111111-2222-4333-8444-555555555555"
BASE = "/api/v3/insight/interactions"
REPORT_Q = f"What is the report {R1} summary?"


class _AuditSink:
    def __init__(self, fail: bool = False) -> None:
        self.entries: list = []
        self.fail = fail

    async def record(self, entry):
        if self.fail:
            raise RuntimeError("audit unavailable")
        self.entries.append(entry)
        return entry

    async def query(self, filters):
        return list(self.entries)


class _Interactions:
    """In-memory stand-in for the append-only Layer-2 repository surface."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.calls: list[dict] = []

    async def create_interaction(self, **kw) -> InsightInteraction:
        row = {
            "id": str(uuid.uuid4()),
            "lifecycle": "received",
            "answer_status": None,
            "narration_state": "not_attempted",
            "provider": None,
            "model": None,
            "model_version": None,
            "tokens_used": None,
            "cost": None,
            "tool_call_count": 0,
            "reference_count": 0,
            "error_class": None,
            "audit_record_id": None,
            "metadata": {},
            **kw,
        }
        self.rows[row["id"]] = row
        return InsightInteraction(**row)

    async def find_by_idempotency_key(self, *, organization_id, idempotency_key):
        for row in self.rows.values():
            if (
                row["organization_id"] == organization_id
                and row.get("idempotency_key") == idempotency_key
            ):
                return InsightInteraction(**row)
        return None

    async def get_interaction(self, *, interaction_id, organization_id, created_by=None):
        row = self.rows.get(interaction_id)
        if not row or row["organization_id"] != organization_id:
            return None
        if created_by is not None and row["created_by"] != created_by:
            return None
        return InsightInteraction(**row)

    async def list_interactions(
        self, *, organization_id, created_by=None, conversation_id=None, limit=50, offset=0
    ):
        rows = [
            r
            for r in self.rows.values()
            if r["organization_id"] == organization_id
            and (created_by is None or r["created_by"] == created_by)
            and (conversation_id is None or r["conversation_id"] == conversation_id)
        ]
        return [InsightInteraction(**r) for r in rows[offset : offset + limit]]

    async def count_interactions(
        self, *, organization_id, created_by=None, conversation_id=None
    ) -> int:
        return len(
            await self.list_interactions(
                organization_id=organization_id,
                created_by=created_by,
                conversation_id=conversation_id,
            )
        )

    async def mark_executing(self, *, interaction_id, organization_id):
        row = self.rows.get(interaction_id)
        if not row or row["lifecycle"] != "received":
            return None
        row["lifecycle"] = "executing"
        return InsightInteraction(**row)

    async def complete_interaction(self, *, interaction_id, organization_id, **kw):
        row = self.rows[interaction_id]
        assert row["lifecycle"] in ("received", "executing"), "append-only violation"
        row.update(kw)
        return InsightInteraction(**row)

    async def record_tool_call(self, *, interaction_id, organization_id, **kw):
        for call in self.calls:
            if (
                call["interaction_id"] == interaction_id
                and call["tool_name"] == kw["tool_name"]
                and call["arguments_hash"] == kw["arguments_hash"]
            ):
                return InsightToolCall(**call)  # idempotent (PO Q10)
        call = {
            "id": str(uuid.uuid4()),
            "interaction_id": interaction_id,
            "organization_id": organization_id,
            **kw,
        }
        self.calls.append(call)
        return InsightToolCall(**call)

    async def list_tool_calls(self, *, interaction_id, organization_id):
        return [
            InsightToolCall(**c) for c in self.calls if c["interaction_id"] == interaction_id
        ]


class _Insight:
    def __init__(self) -> None:
        self.conversations: dict[str, dict] = {}
        self.messages: list[dict] = []

    def add_conversation(self, conversation_id, organization_id, created_by):
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "organization_id": organization_id,
            "created_by": created_by,
        }

    async def get_conversation(self, *, conversation_id, organization_id):
        row = self.conversations.get(conversation_id)
        if row and row["organization_id"] == organization_id:
            return SimpleNamespace(**row)
        return None

    async def add_message(self, **kw):
        message = {"id": str(uuid.uuid4()), **kw}
        self.messages.append(message)
        return SimpleNamespace(**message)


class _Orgs:
    def __init__(self, active=(ORG_A,)) -> None:
        self.active = set(active)

    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=organization_id in self.active)


class _NoneRepo:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


class _World:
    def __init__(self, active=(ORG_A,), audit_fail=False) -> None:
        self.jsonb = None
        self.insight = _Insight()
        self.interactions = _Interactions()
        self.audit = _AuditSink(fail=audit_fail)
        self.orgs = _Orgs(active)
        self.staff = _NoneRepo()
        self.consultants = _NoneRepo()
        self.reports_rows: dict[str, dict] = {}

    def bundle(self):
        reports = self

        class _Reports:
            async def get_full(self, report_id):
                return reports.reports_rows.get(report_id)

        return SimpleNamespace(
            reports=_Reports(),
            report_versions=None,
            disclosure_projection=None,
            logs=None,
            organizations=self.orgs,
            staff=self.staff,
            consultants=self.consultants,
            insight=self.insight,
            insight_interactions=self.interactions,
            audit=self.audit,
            # Phase 8 I8-A — the shared rate-limit store (same semantics, in memory).
            insight_limits=InsightLimitsFake(),
        )


def _user(user_id, organization_id=ORG_A, is_member=True):
    return AuthUser(
        user_id=user_id,
        email=f"{user_id[:4]}@example.test",
        role="org_owner",
        role_name="org_owner",
        organization_id=organization_id,
        is_org_member=is_member,
    )


@pytest.fixture()
def world():
    return _World()


@pytest.fixture()
def api(world, monkeypatch):
    app = FastAPI()
    app.include_router(api_mod.router)
    state = SimpleNamespace(user=_user(ALICE), client=None)

    async def _current_user():
        return state.user

    async def _repositories():
        return world.bundle()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    monkeypatch.setattr(api_mod, "narration_client", lambda: state.client)
    world.insight.add_conversation(C1, ORG_A, ALICE)
    return SimpleNamespace(client=TestClient(app), world=world, state=state)


def _stub_tool(monkeypatch, status=ToolStatus.SUCCESS, *, data=None, refs=None, reason=None):
    calls: list[dict] = []

    async def fake_invoke_tool(*, tool_name, current_user, repos, organization_id, tool_input):
        calls.append({"tool": tool_name, "input": dict(tool_input)})
        return ToolResult(
            tool=tool_name,
            status=status,
            data=dict(data or {}),
            references=tuple(
                InsightReference(kind=k, id=i) for k, i in (refs or (("report", R1),))
            ),
            reason=reason,
        )

    monkeypatch.setattr(svc, "invoke_tool", fake_invoke_tool)
    return calls


def _post(api, question=REPORT_Q, **kw):
    body = {"organization_id": ORG_A, "conversation_id": C1, "question": question}
    body.update(kw)
    return api.client.post(BASE, json=body)


# -- persistence, correlation, audit ---------------------------------------
def test_success_interaction_persists_layer2_evidence_and_audit(api, monkeypatch):
    calls = _stub_tool(monkeypatch, data={"lines": [1, 2, 3]})
    response = _post(api)
    assert response.status_code == 201
    body = response.json()
    assert body["answer_status"] == "success"
    assert body["lifecycle"] == "completed"
    assert body["contract_version"] == INTERACTION_CONTRACT_VERSION
    assert len(body["tool_calls"]) == 1
    assert body["tool_calls"][0]["tool"] == "report_lookup"
    assert {"kind": "report", "id": R1} in body["references"]
    assert calls[0]["input"] == {"report_id": R1}
    assert body["tokens_used"] is None and body["cost"] is None
    entry = api.world.audit.entries[-1]
    assert entry.correlation_id == body["interaction_id"]
    assert entry.changed_fields["tool_call_ids"] == [body["tool_calls"][0]["tool_call_id"]]
    assert entry.changed_fields["answer_status"] == "success"
    assert entry.entity_id == body["interaction_id"]
    assert api.world.interactions.rows[body["interaction_id"]]["audit_record_id"] == entry.id


def test_raw_question_lives_only_in_the_i1_message_layer(api, monkeypatch):
    _stub_tool(monkeypatch)
    body = _post(api).json()
    assert [m for m in api.world.insight.messages if m["role"] == "user"][0]["content"] == REPORT_Q
    row = api.world.interactions.rows[body["interaction_id"]]
    assert row["question_hash"] == svc.hash_text(REPORT_Q)
    assert REPORT_Q not in json.dumps(row, default=str)


def test_tool_call_evidence_is_idempotent_per_logical_call(api, monkeypatch):
    _stub_tool(monkeypatch)
    first = _post(api, idempotency_key="k-1").json()
    second = _post(api, idempotency_key="k-1").json()
    assert second["replayed"] is True
    assert second["interaction_id"] == first["interaction_id"]
    assert len(api.world.interactions.rows) == 1
    assert len(api.world.interactions.calls) == 1


def test_no_unrestricted_payload_or_url_is_persisted(api, monkeypatch):
    _stub_tool(
        monkeypatch,
        data={
            "lines": [{"raw_description": "SECRET", "final_report_url": "https://x/y"}],
            "content": "SECRET",
        },
    )
    body = _post(api).json()
    stored = json.dumps(api.world.interactions.calls, default=str)
    for forbidden in ("SECRET", "final_report_url", "content", "https://x/y"):
        assert forbidden not in stored
    assert len(body["tool_calls"]) == 1


# -- answer-state mapping (PO Q3) ------------------------------------------
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (ToolStatus.NO_DATA, "no_data"),
        (ToolStatus.NOT_AUTHORIZED, "not_authorized"),
        (ToolStatus.INVALID_INPUT, "invalid_input"),
        (ToolStatus.ERROR, "error"),
    ],
)
def test_tool_status_maps_to_the_i4_answer_vocabulary(api, monkeypatch, status, expected):
    _stub_tool(monkeypatch, status=status, reason="stub")
    body = _post(api).json()
    assert body["answer_status"] == expected
    assert body["tool_calls"][0]["status"] == str(status)
    assert body["lifecycle"] == ("failed" if expected == "error" else "completed")


def test_intent_refusals_use_clarification_and_refusal_states(api, monkeypatch):
    _stub_tool(monkeypatch)
    ambiguous = _post(api, "Show the report version evidence").json()
    assert ambiguous["answer_status"] == "needs_clarification"
    assert ambiguous["tool_calls"] == []
    unsupported = _post(api, "Hello CarbonTally").json()
    assert unsupported["answer_status"] == "refused"
    no_identifier = _post(api, "What is the report summary?").json()
    assert no_identifier["answer_status"] == "needs_clarification"


def test_i4_answer_vocabulary_is_the_ratified_states():
    """The fourteen Master Spec §14 states plus the authorized ``multiple_matches``.

    ``multiple_matches`` was authorized by the PO Insight
    Discovery-Aggregation-Provenance package (2026-09-22) so a bounded discovery
    that matches several authoritative records is reported truthfully instead of
    being silently converted into ``success``.
    """
    assert {s.value for s in AnswerStatus} == {
        "success", "zero", "no_data", "not_authorized", "insufficient_data",
        "needs_clarification", "multiple_matches", "tool_failure",
        "provider_unavailable", "partial", "rate_limited", "refused", "ungrounded",
        "invalid_input", "error",
    }
    assert set(ALLOWED_TOOL_STATUSES) == {
        "success", "no_data", "not_authorized", "invalid_input",
        "provider_unavailable", "error",
    }


# -- provider behaviour (PO Q11/Q14) ---------------------------------------
class _FailingClient:
    async def complete(self, prompt, *, system=None, temperature=0.0, max_tokens=512):
        raise RuntimeError("provider down")


class _WorkingClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def complete(self, prompt, *, system=None, temperature=0.0, max_tokens=512):
        self.prompts.append(prompt)
        return "Grounded explanation of the authorised evidence."


def test_optional_narration_failure_keeps_the_deterministic_answer(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.state.client = _FailingClient()
    body = _post(api).json()
    assert body["answer_status"] == "success"
    assert body["narration_state"] == "unavailable"
    assert body["narration_text"] is None
    assert body["references"] == [{"kind": "report", "id": R1}]


def test_required_narration_failure_is_provider_unavailable_without_fabrication(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.state.client = _FailingClient()
    body = _post(api, narration="required").json()
    assert body["answer_status"] == "provider_unavailable"
    assert body["narration_state"] == "unavailable"
    assert body["narration_text"] is None
    assert body["references"] == [{"kind": "report", "id": R1}]


def test_required_narration_without_a_configured_provider_is_truthful(api, monkeypatch):
    _stub_tool(monkeypatch)
    body = _post(api, narration="required").json()
    assert body["answer_status"] == "provider_unavailable"
    assert body["provider"] is None and body["model"] is None


def test_optional_narration_without_a_provider_is_skipped(api, monkeypatch):
    _stub_tool(monkeypatch)
    body = _post(api).json()
    assert body["narration_state"] == "skipped"
    assert body["provider"] is None


def test_narration_records_truthful_attribution_and_appends_a_message(api, monkeypatch, monkeypatch_env=None):
    _stub_tool(monkeypatch)
    monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.example-provider.test/v1")
    monkeypatch.setenv("CARBONTALLY_AI_API_KEY", "test-key-not-a-secret")
    monkeypatch.setenv("CARBONTALLY_AI_MODEL", "example-model-1")
    client = _WorkingClient()
    api.state.client = client
    body = _post(api).json()
    assert body["narration_state"] == "completed"
    assert body["narration_text"].startswith("Grounded")
    assert body["provider"] == "api.example-provider.test"
    assert body["model"] == "example-model-1"
    assert REPORT_Q[:20] in client.prompts[0]
    assert [m for m in api.world.insight.messages if m["role"] == "insight"][0]["content"] == body["narration_text"]


# -- authorization (PO Q8) -------------------------------------------------
def test_cross_organisation_access_is_denied_before_any_evidence(api, monkeypatch):
    _stub_tool(monkeypatch)
    response = _post(api, organization_id=ORG_B)
    assert response.status_code == 403
    assert api.world.interactions.rows == {}
    assert api.world.insight.messages == []


def test_inactive_organisation_is_denied(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.world.orgs.active = set()
    assert _post(api).status_code == 403
    assert api.world.interactions.rows == {}


def test_creator_private_reads_do_not_disclose_other_creators(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.world.insight.add_conversation(str(uuid.uuid4()), ORG_A, BOB)
    api.state.user = _user(BOB)
    bob_conversation = [c for c, row in api.world.insight.conversations.items() if row["created_by"] == BOB][0]
    bob = _post(api, conversation_id=bob_conversation).json()
    api.state.user = _user(ALICE)
    assert api.client.get(
        f"{BASE}/{bob['interaction_id']}", params={"organization_id": ORG_A}
    ).status_code == 404
    assert _post(api, conversation_id=bob_conversation).status_code == 404
    listed = api.client.get(BASE, params={"organization_id": ORG_A}).json()
    assert [i["interaction_id"] for i in listed["interactions"]] != [bob["interaction_id"]]


def test_invalid_input_fails_closed_without_persistence(api, monkeypatch):
    _stub_tool(monkeypatch)
    assert _post(api, question="   ").status_code == 422
    assert _post(api, question="x" * 2001).status_code == 422
    assert _post(api, narration="sometimes").status_code == 422
    assert api.world.interactions.rows == {}


def test_audit_failure_makes_the_interaction_truthfully_failed(monkeypatch):
    world = _World(audit_fail=True)
    _stub_tool(monkeypatch)
    monkeypatch.setattr(api_mod, "narration_client", lambda: None)
    app = FastAPI()
    app.include_router(api_mod.router)
    world.insight.add_conversation(C1, ORG_A, ALICE)

    async def _current_user():
        return _user(ALICE)

    async def _repositories():
        return world.bundle()

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    client = TestClient(app)
    body = client.post(
        BASE,
        json={"organization_id": ORG_A, "conversation_id": C1, "question": REPORT_Q},
    ).json()
    assert body["answer_status"] == "error"
    assert body["lifecycle"] == "failed"
    assert body["audit_record_id"] is None
