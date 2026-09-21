"""I5 — bounded deterministic context assembly (PO I5 decisions, 2026-09-21).

Covers the authorized I5 behaviour exactly: current-conversation context only;
deterministic bounded selection; chronological ordering; most-recent preference
within a configurable budget (default 20,000 characters); the current question
preserved; deterministic truncation; empty context as a normal condition that
never becomes ``zero``; history never authoritative; references as locators; no
cross-scope reads; bounded structured tool projections; no audit injection; no
summarisation and no persistence of any kind.

In-memory only: no database, no provider, no network.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from auth import AuthUser
from services import insight_context as ctx

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CONV_A = "cccccccc-1111-4111-8111-111111111111"
CONV_B = "cccccccc-2222-4222-8222-222222222222"
SECRET = "SECRET-RAW-PAYLOAD-DO-NOT-LEAK"

_BASE = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)


@dataclass
class _Call:
    tool_name: str = "report_lookup"
    tool_status: str = "success"
    result_metadata: dict = field(default_factory=lambda: {"reason": None})
    result_item_count: int = 2
    truncated: bool = False
    duration_ms: int = 5
    contract_version: str = "i3-6point-v1"
    references: tuple = ({"kind": "report", "id": "ref-1"},)
    # Forbidden payload material the projection must never carry:
    arguments: dict = field(default_factory=lambda: {"raw": SECRET})
    result_data: dict = field(default_factory=lambda: {"payload": SECRET})


class _Interactions:
    """Records every call so tests can prove read-only, scoped behaviour."""

    def __init__(self) -> None:
        self.rows: dict[str, list[SimpleNamespace]] = {}
        self.calls: dict[str, list[_Call]] = {}
        self.reads: list[dict] = []

    def add(self, conversation_id, index, *, created_at, answer_status="success", calls=()):
        interaction_id = f"i-{conversation_id[-4:]}-{index}"
        self.rows.setdefault(conversation_id, []).append(
            SimpleNamespace(
                id=interaction_id,
                conversation_id=conversation_id,
                created_at=created_at,
                lifecycle="completed",
                answer_status=answer_status,
                narration_state="completed",
                intent="report_lookup",
            )
        )
        self.calls[interaction_id] = list(calls)
        return interaction_id

    async def list_interactions(
        self, *, organization_id, created_by=None, conversation_id=None, limit=50, offset=0
    ):
        self.reads.append(
            {
                "method": "list_interactions",
                "organization_id": organization_id,
                "created_by": created_by,
                "conversation_id": conversation_id,
                "limit": limit,
                "offset": offset,
            }
        )
        rows = list(self.rows.get(conversation_id, []))
        rows.sort(key=lambda r: (r.created_at, r.id), reverse=True)
        return rows[offset : offset + limit]

    async def list_tool_calls(self, *, interaction_id, organization_id):
        self.reads.append({"method": "list_tool_calls", "interaction_id": interaction_id})
        return list(self.calls.get(interaction_id, []))


class _Insight:
    def __init__(self) -> None:
        self.conversations: dict[str, SimpleNamespace] = {}

    def add_conversation(self, conversation_id, organization_id, created_by):
        self.conversations[conversation_id] = SimpleNamespace(
            id=conversation_id, organization_id=organization_id, created_by=created_by
        )

    async def get_conversation(self, *, conversation_id, organization_id):
        row = self.conversations.get(conversation_id)
        if row is not None and row.organization_id == organization_id:
            return row
        return None


class _Orgs:
    def __init__(self, active=(ORG_A,)):
        self.active = set(active)

    async def get_by_id(self, organization_id):
        return SimpleNamespace(id=organization_id, is_active=organization_id in self.active)


class _None:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


class _AuditForbidden:
    """Any audit access proves the assembler injected audit context (PO I5-7)."""

    async def record(self, entry):
        raise AssertionError("audit must not be used as conversational context")

    async def query(self, filters):
        raise AssertionError("audit must not be queried to assemble context")


class _World:
    def __init__(self, active=(ORG_A,)):
        self.interactions = _Interactions()
        self.insight = _Insight()
        self.orgs = _Orgs(active)
        self.staff = _None()
        self.consultants = _None()
        self.audit = _AuditForbidden()
        self.insight.add_conversation(CONV_A, ORG_A, ALICE)
        self.insight.add_conversation(CONV_B, ORG_A, ALICE)

    def bundle(self):
        return SimpleNamespace(
            organizations=self.orgs,
            staff=self.staff,
            consultants=self.consultants,
            insight=self.insight,
            insight_interactions=self.interactions,
            audit=self.audit,
        )


def _user(user_id=ALICE, organization_id=ORG_A):
    return AuthUser(
        user_id=user_id,
        email=f"{user_id[:4]}@example.test",
        role="org_owner",
        role_name="org_owner",
        organization_id=organization_id,
        is_org_member=True,
    )


async def _assemble(world, *, question="What is the report summary?", conversation=CONV_A, **kw):
    return await ctx.assemble_context(
        current_user=_user(),
        repos=world.bundle(),
        organization_id=ORG_A,
        conversation_id=conversation,
        question=question,
        **kw,
    )


def _seed(world, count, *, conversation=CONV_A, step_seconds=60, calls=()):
    ids = []
    for index in range(count):
        ids.append(
            world.interactions.add(
                conversation,
                index,
                created_at=_BASE + timedelta(seconds=index * step_seconds),
                calls=calls,
            )
        )
    return ids


# ---------------------------------------------------------------- assembly --
async def test_current_conversation_context_is_assembled():
    world = _World()
    ids = _seed(world, 3)
    context = await _assemble(world)
    assert context.interaction_count == 3
    assert {b.interaction_id for b in context.blocks} == set(ids)
    assert context.policy_version == ctx.CONTEXT_POLICY_VERSION


async def test_unrelated_conversations_are_not_included():
    world = _World()
    _seed(world, 2, conversation=CONV_A)
    foreign = _seed(world, 2, conversation=CONV_B)
    context = await _assemble(world)
    assert context.interaction_count == 2
    assert all(b.interaction_id not in foreign for b in context.blocks)
    # the only conversation scoped in the query is the current one
    scoped = {r.get("conversation_id") for r in world.interactions.reads if r["method"] == "list_interactions"}
    assert scoped == {CONV_A}
    assert all(r["created_by"] == ALICE for r in world.interactions.reads if r["method"] == "list_interactions")


async def test_ordering_is_chronological_and_deterministic():
    world = _World()
    _seed(world, 4)
    first = await _assemble(world)
    second = await _assemble(world)
    times = [b.created_at for b in first.blocks]
    assert times == sorted(times)
    assert first.history_text == second.history_text
    assert first.as_dict() == second.as_dict()


async def test_recent_material_is_selected_within_the_budget():
    world = _World()
    ids = _seed(world, 4)
    context = await _assemble(world, max_chars=250)
    assert context.truncated is True
    assert ids[-1] in {b.interaction_id for b in context.blocks}
    assert len(context.history_text) <= 250


async def test_assembled_history_never_exceeds_the_configured_budget():
    world = _World()
    _seed(world, 40, calls=[_Call() for _ in range(4)])
    for budget in (200, 1_000, 5_000, ctx.DEFAULT_MAX_HISTORY_CHARS):
        context = await _assemble(world, max_chars=budget)
        assert len(context.history_text) <= budget, budget
        assert context.max_chars == budget


def test_the_ratified_default_budget_is_twenty_thousand_characters():
    assert ctx.DEFAULT_MAX_HISTORY_CHARS == 20_000
    assert ctx.configured_max_history_chars() == 20_000


def test_the_budget_is_configurable_and_bad_configuration_fails_safe(monkeypatch):
    monkeypatch.setenv("CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS", "500")
    assert ctx.configured_max_history_chars() == 500
    monkeypatch.setenv("CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS", "not-a-number")
    assert ctx.configured_max_history_chars() == ctx.DEFAULT_MAX_HISTORY_CHARS
    monkeypatch.setenv("CARBONTALLY_INSIGHT_CONTEXT_MAX_CHARS", "0")
    assert ctx.configured_max_history_chars() == ctx.DEFAULT_MAX_HISTORY_CHARS


async def test_current_question_is_preserved_verbatim():
    world = _World()
    question = "What is the calculation snapshot for 44444444-5555-4666-8777-888888888888?"
    context = await _assemble(world, question=question)
    assert context.question == question
    sections = ctx.context_prompt_sections(context)
    assert sections["current_question"] == question
    assert sections["historical_context_is_authoritative"] == "false"


async def test_truncation_is_deterministic():
    world = _World()
    _seed(world, 6, calls=[_Call() for _ in range(4)])
    a = await _assemble(world, max_chars=400)
    b = await _assemble(world, max_chars=400)
    assert a.truncated and b.truncated
    assert [x.interaction_id for x in a.blocks] == [x.interaction_id for x in b.blocks]
    assert a.history_text == b.history_text


# --------------------------------------------------------------- emptiness --
async def test_empty_context_is_valid_and_not_an_error():
    world = _World()
    context = await _assemble(world)
    assert context.empty is True
    assert context.history_text == ""
    sections = ctx.context_prompt_sections(context)
    assert sections["historical_context_is_empty"] == "true"
    assert sections["historical_context"] == "(no prior conversation context)"
    assert sections["current_question"]


async def test_empty_context_never_becomes_zero():
    world = _World()
    context = await _assemble(world)
    # No blocks are fabricated, and no "zero" evidence is manufactured.
    assert context.blocks == ()
    assert json.loads(json.dumps(context.as_dict()))["interaction_count"] == 0
    assert "zero" not in context.history_text


# --------------------------------------------------- authorization / scope --
async def test_cross_scope_context_cannot_be_loaded():
    world = _World()
    # another org entirely
    with pytest.raises(HTTPException) as cross_org:
        await ctx.assemble_context(
            current_user=_user(), repos=world.bundle(), organization_id=ORG_B,
            conversation_id=CONV_A, question="q",
        )
    assert cross_org.value.status_code == 403
    # inactive organisation
    world.orgs.active = set()
    with pytest.raises(HTTPException) as inactive:
        await _assemble(world)
    assert inactive.value.status_code == 403
    world.orgs.active = {ORG_A}
    # another creator's conversation is not loaded (existence not disclosed)
    with pytest.raises(HTTPException) as foreign:
        await ctx.assemble_context(
            current_user=_user(BOB), repos=world.bundle(), organization_id=ORG_A,
            conversation_id=CONV_A, question="q",
        )
    assert foreign.value.status_code == 404


async def test_history_is_never_authoritative_and_grant_nothing():
    world = _World()
    _seed(world, 1)
    context = await _assemble(world)
    block = context.blocks[0]
    assert block.authoritative is False
    assert block.as_dict()["evidence_class"] == ctx.EVIDENCE_CLASS_HISTORY
    # references are locators only: nothing was resolved, and no resource
    # repository is even present on the bundle used here.
    assert all(set(ref) == {"kind", "id"} for ref in block.references)
    assert not hasattr(world.bundle(), "reports")


# ------------------------------------------------ projection / privacy ------ 
async def test_only_bounded_structured_tool_projections_are_used():
    world = _World()
    _seed(world, 2, calls=[_Call(), _Call(tool_name="calculation_snapshot_lookup")])
    context = await _assemble(world)
    assert SECRET not in context.history_text
    for block in context.blocks:
        for call in block.tool_calls:
            assert set(call) <= {
                "tool", "status", "reason", "contract_version",
                "result_item_count", "truncated", "duration_ms", "reference_kinds",
            }
            assert "arguments" not in call and "result_data" not in call
    assert "reference_kinds" in context.blocks[0].tool_calls[0]


async def test_audit_records_are_not_injected_into_context():
    world = _World()
    _seed(world, 2)
    # _AuditForbidden raises on ANY access, so completing this proves PO I5-7.
    context = await _assemble(world)
    assert context.interaction_count == 2


async def test_no_persistence_no_summarisation_no_cross_conversation_memory():
    import ast
    import inspect

    # Scan CODE only: strip docstrings (which legitimately *describe* the things
    # I5 must not do) before asserting none of them is implemented.
    tree = ast.parse(inspect.getsource(ctx))
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(
            node.body[0].value, ast.Constant
        ) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
    source = ast.unparse(tree)
    for forbidden in (
        "INSERT", "UPDATE", "DELETE", "dumps_jsonb", "save(", "create_interaction",
        "record_tool_call", "summar", "embedding", "vector", "langchain", "tiktoken",
    ):
        assert forbidden.lower() not in source.lower(), forbidden
    world = _World()
    _seed(world, 2)
    await _assemble(world)
    methods = {r["method"] for r in world.interactions.reads}
    assert methods <= {"list_interactions", "list_tool_calls"}


async def test_a_prior_interaction_can_be_excluded_from_its_own_context():
    world = _World()
    ids = _seed(world, 3)
    context = await _assemble(world, exclude_interaction_id=ids[-1])
    assert ids[-1] not in {b.interaction_id for b in context.blocks}
    assert context.interaction_count == 2


async def test_invalid_budget_is_refused():
    world = _World()
    with pytest.raises(HTTPException) as exc:
        await _assemble(world, max_chars=0)
    assert exc.value.status_code == 422
