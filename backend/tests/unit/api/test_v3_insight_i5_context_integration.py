"""I5 integration — bounded history reaches the provider call, and nothing else changes.

Proves the authorized I5 behaviour on the real HTTP path: the ratified
20,000-character budget is enforced **before provider submission**; history is
labelled non-authoritative; the current authoritative tool evidence is unchanged;
an empty history is normal and never becomes ``zero``; historical references grant
nothing; and no context is assembled when no provider narration is attempted.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from api import v3_insight_interactions as api_mod
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from domain.insight_tool import InsightReference, ToolResult, ToolStatus
from services import insight_context as ctx
from services import insight_interactions as svc
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CONV = "cccccccc-1111-4111-8111-111111111111"
R1 = "11111111-2222-4333-8444-555555555555"
FOREIGN_REF = "99999999-8888-4777-8666-555555555555"
BASE = "/api/v3/insight/interactions"
QUESTION = f"What is the report {R1} summary?"
CURRENT_MARKER = "AUTHORITATIVE-CURRENT-RESULT-MARKER"
_BASE_TIME = datetime(2026, 9, 21, 9, 0, 0, tzinfo=timezone.utc)


class _AuditSink:
    def __init__(self):
        self.entries = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry

    async def query(self, filters):
        return list(self.entries)


class _History:
    """Prior-interaction store: newest-first reads, creator-private, read-only."""

    def __init__(self):
        self.rows = []
        self.calls = {}
        self.writes = []

    def seed(self, index, *, answer_status="success", refs=({"kind": "report", "id": FOREIGN_REF},)):
        row = SimpleNamespace(
            id=f"hist-{index}",
            conversation_id=CONV,
            created_at=_BASE_TIME + timedelta(minutes=index),
            lifecycle="completed",
            answer_status=answer_status,
            narration_state="completed",
            intent="report_lookup",
        )
        self.rows.append(row)
        self.calls[row.id] = [
            SimpleNamespace(
                tool_name="report_lookup", tool_status="success",
                result_metadata={"reason": None}, result_item_count=1,
                truncated=False, duration_ms=3, contract_version="i3-6point-v1",
                references=refs,
            )
        ]
        return row.id

    async def list_interactions(self, *, organization_id, created_by=None, conversation_id=None, limit=50, offset=0):
        rows = [r for r in self.rows if r.conversation_id == conversation_id]
        rows.sort(key=lambda r: (r.created_at, r.id), reverse=True)
        return rows[offset : offset + limit]

    async def list_tool_calls(self, *, interaction_id, organization_id):
        return list(self.calls.get(interaction_id, []))


class _NewInteractions:
    """The I4 write surface the orchestration uses (unchanged behaviour)."""

    def __init__(self):
        self.rows = {}
        self.tool_calls = []

    async def create_interaction(self, **kw):
        row = dict(
            id=str(uuid.uuid4()), lifecycle="received", answer_status=None,
            narration_state="not_attempted", provider=None, model=None, model_version=None,
            tokens_used=None, cost=None, tool_call_count=0, reference_count=0,
            error_class=None, audit_record_id=None, metadata={}, **kw,
        )
        self.rows[row["id"]] = row
        return SimpleNamespace(**row)

    async def find_by_idempotency_key(self, *, organization_id, idempotency_key):
        return None

    async def get_interaction(self, *, interaction_id, organization_id, created_by=None):
        return None

    async def list_interactions(self, **kw):
        return []

    async def count_interactions(self, **kw):
        return 0

    async def mark_executing(self, *, interaction_id, organization_id):
        self.rows[interaction_id]["lifecycle"] = "executing"
        return SimpleNamespace(**self.rows[interaction_id])

    async def complete_interaction(self, *, interaction_id, organization_id, **kw):
        self.rows[interaction_id].update(kw)
        return SimpleNamespace(**self.rows[interaction_id])

    async def record_tool_call(self, *, interaction_id, organization_id, **kw):
        row = {"id": str(uuid.uuid4()), "interaction_id": interaction_id,
               "organization_id": organization_id, **kw}
        self.tool_calls.append(row)
        return SimpleNamespace(**row)

    async def list_tool_calls(self, **kw):
        return []


class _Insight:
    def __init__(self):
        self.conversations = {
            CONV: SimpleNamespace(id=CONV, organization_id=ORG_A, created_by=ALICE)
        }
        self.messages = []

    async def get_conversation(self, *, conversation_id, organization_id):
        row = self.conversations.get(conversation_id)
        return row if row and row.organization_id == organization_id else None

    async def add_message(self, **kw):
        message = {"id": str(uuid.uuid4()), **kw}
        self.messages.append(message)
        return SimpleNamespace(**message)


class _Orgs:
    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=True)


class _None:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


class _Client:
    def __init__(self):
        self.prompts = []

    async def complete(self, prompt, *, system=None, temperature=0.0, max_tokens=512):
        self.prompts.append(prompt)
        return "Grounded explanation."


class _World:
    def __init__(self):
        self.history = _History()
        self.interactions = _NewInteractions()
        self.insight = _Insight()
        self.audit = _AuditSink()
        self.bundle = SimpleNamespace(
            organizations=_Orgs(), staff=_None(), consultants=_None(),
            insight=self.insight, insight_interactions=self.interactions, audit=self.audit,
            insight_limits=InsightLimitsFake(),
        )


def _user():
    return AuthUser(
        user_id=ALICE, email="alice@example.test", role="org_owner",
        role_name="org_owner", organization_id=ORG_A, is_org_member=True,
    )


@pytest.fixture()
def api(monkeypatch):
    """Real router + real service; only the persistence bundle and auth are faked."""
    world = _World()
    # The assembler reads history; the orchestration writes Layer-2 evidence.
    combined = world.bundle
    combined.insight_interactions = world.history  # reads
    writes = world.interactions

    class _Router(SimpleNamespace):
        pass

    # Route read vs write by method name: the assembler only reads history.
    class _DualProxy:
        def __getattr__(self, name):
            if hasattr(world.history, name):
                return getattr(world.history, name)
            return getattr(writes, name)

    combined.insight_interactions = _DualProxy()

    app = FastAPI()
    app.include_router(api_mod.router)
    state = SimpleNamespace(client=_Client(), assembler_calls=0)

    async def _current_user():
        return _user()

    async def _repositories():
        return combined

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    monkeypatch.setattr(api_mod, "narration_client", lambda: state.client)

    real_assemble = svc.assemble_context

    async def _spy_assembler(**kwargs):
        state.assembler_calls += 1
        return await real_assemble(**kwargs)

    monkeypatch.setattr(svc, "assemble_context", _spy_assembler)
    return SimpleNamespace(
        client=TestClient(app), world=world, state=state, bundle=combined
    )


def _stub_tool(monkeypatch, status=ToolStatus.SUCCESS, *, data=None):
    async def fake_invoke_tool(*, tool_name, current_user, repos, organization_id, tool_input):
        return ToolResult(
            tool=tool_name, status=status, data=dict(data or {"note": CURRENT_MARKER}),
            references=(InsightReference(kind="report", id=R1),), reason=None,
        )

    monkeypatch.setattr(svc, "invoke_tool", fake_invoke_tool)


def _post(api, **kw):
    body = {"organization_id": ORG_A, "conversation_id": CONV, "question": QUESTION}
    body.update(kw)
    return api.client.post(BASE, json=body)


# -------------------------------------------------------------- integration --
def test_prompt_carries_bounded_history_labelled_non_authoritative(api, monkeypatch):
    _stub_tool(monkeypatch)
    ids = [api.world.history.seed(i) for i in range(3)]
    response = _post(api)
    assert response.status_code == 201
    prompt = api.state.client.prompts[0]
    assert "NOT authoritative" in prompt
    assert all(i in prompt for i in ids)          # current-conversation history present
    assert CURRENT_MARKER in prompt               # current authoritative evidence present
    history = prompt.split("Prior conversation context", 1)[1]
    assert len(history) <= ctx.DEFAULT_MAX_HISTORY_CHARS
    assert response.json()["answer_status"] == "success"


def test_history_budget_is_enforced_before_provider_submission(api, monkeypatch):
    _stub_tool(monkeypatch)
    for i in range(30):
        api.world.history.seed(i)
    monkeypatch.setenv("CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS", "500")
    _post(api)
    small = api.state.client.prompts[-1]
    monkeypatch.setenv("CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS", "20000")
    _post(api)
    large = api.state.client.prompts[-1]
    small_history = small.split("Prior conversation context", 1)[1]
    large_history = large.split("Prior conversation context", 1)[1]
    assert len(small_history) < len(large_history)
    # A 500-character budget admits only the most recent material, far fewer than
    # the 30 seeded interactions; the larger budget admits noticeably more.
    assert small_history.count("interaction_id") < large_history.count("interaction_id")
    assert small_history.count("interaction_id") <= 3


def test_empty_history_is_normal_and_never_becomes_zero(api, monkeypatch):
    _stub_tool(monkeypatch)
    body = _post(api).json()
    assert body["answer_status"] == "success"
    prompt = api.state.client.prompts[0]
    assert "(no prior conversation context)" in prompt
    assert "zero" not in body["answer_status"]
    _stub_tool(monkeypatch, status=ToolStatus.NO_DATA)
    assert _post(api).json()["answer_status"] == "no_data"


def test_historical_references_do_not_grant_or_trigger_anything(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.world.history.seed(1)
    body = _post(api).json()
    prompt = api.state.client.prompts[0]
    assert FOREIGN_REF in prompt                  # shown as a locator only
    assert len(body["tool_calls"]) == 1           # exactly the current tool call
    assert FOREIGN_REF not in json.dumps(body["references"])


def test_no_context_is_assembled_without_provider_narration(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.world.history.seed(1)
    body = _post(api, narration="none").json()
    assert body["narration_state"] == "skipped"
    assert api.state.assembler_calls == 0
    assert api.state.client.prompts == []


def test_context_assembly_is_read_only(api, monkeypatch):
    _stub_tool(monkeypatch)
    api.world.history.seed(1)
    before = len(api.world.history.rows)
    _post(api)
    assert len(api.world.history.rows) == before          # no history writes
    assert len(api.world.interactions.tool_calls) == 1    # exactly the current call
    assert len(api.world.interactions.rows) == 1          # exactly the current interaction
