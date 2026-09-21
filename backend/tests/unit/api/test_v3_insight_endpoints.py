"""I1 — CarbonTally Insight persistence API: authorization + organisation isolation.

Authorisation: CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.

Verifies the ratified I1 boundaries (D2 §8 authorization — every read
re-authorised and a stored reference is not a grant; §9.2 creator-private
visibility; §24.2 the I1 MAY-include persistence surface):

* create / list / read conversations, append + list messages;
* creator-private visibility within an organisation;
* organisation isolation (no cross-tenant read or write);
* no LLM, no answer generation: an ``insight``-authored message cannot be
  persisted through the API in I1.

The suite is in-memory: the production repository is replaced through the
FastAPI dependency overrides, so no database is opened.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from api import v3_insight
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from domain.insight import InsightConversation, InsightMessage

ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
BASE = "/api/v3/insight"


class InMemoryInsightRepository:
    """In-memory stand-in for the I1 repository surface the router consumes."""

    def __init__(self) -> None:
        self.conversations: dict[str, InsightConversation] = {}
        self.messages: dict[str, list[InsightMessage]] = {}
        self.writes = 0

    async def create_conversation(self, *, organization_id, created_by, title=None):
        cid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        conversation = InsightConversation(
            id=cid,
            organization_id=organization_id,
            created_by=created_by,
            title=title,
            created_at=now,
            updated_at=now,
        )
        self.conversations[cid] = conversation
        self.writes += 1
        return conversation

    async def list_conversations(self, *, organization_id, created_by=None, limit=50, offset=0):
        rows = [
            c
            for c in self.conversations.values()
            if c.organization_id == organization_id
            and (created_by is None or c.created_by == created_by)
        ]
        rows.sort(key=lambda c: c.created_at, reverse=True)
        return rows[offset : offset + limit]

    async def get_conversation(self, *, conversation_id, organization_id):
        conversation = self.conversations.get(conversation_id)
        if conversation and conversation.organization_id == organization_id:
            return conversation
        return None

    async def add_message(self, *, conversation_id, organization_id, role, content, created_by=None):
        existing = self.messages.get(conversation_id, [])
        message = InsightMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            organization_id=organization_id,
            created_by=created_by,
            role=role,
            content=content,
            ordinal=(max(m.ordinal for m in existing) if existing else 0) + 1,
            created_at=datetime.now(timezone.utc),
        )
        self.messages.setdefault(conversation_id, []).append(message)
        self.writes += 1
        return message

    async def list_messages(self, *, conversation_id, organization_id, limit=200, offset=0):
        rows = [
            m
            for m in self.messages.get(conversation_id, [])
            if m.organization_id == organization_id
        ]
        rows.sort(key=lambda m: m.ordinal)
        return rows[offset : offset + limit]

    async def count_conversations(self, *, organization_id, created_by=None):
        return len(
            await self.list_conversations(
                organization_id=organization_id, created_by=created_by, limit=100000
            )
        )


def _bundle(repo):
    """Minimal bundle for the I1 router.

    ``insight`` is the only repository the router consumes directly; ``staff`` and
    ``consultants`` are the surfaces the I2 authorization layer resolves (both
    return "no relationship" here, so these tests exercise the customer path).
    """

    class _NoStaff:
        async def get_by_user(self, user_id):
            return None

        async def get_role(self, role_id):
            return None

    class _NoConsultant:
        async def get_active_memberships_by_user(self, user_id):
            return []

        async def get_profile_by_id(self, profile_id):
            return None

        async def get_client_by_org(self, consultant_id, organization_id):
            return None

    class _OrgRepo:
        """Active-organisation stub for the Insight org-active check (OHD F-02)."""

        async def get_by_id(self, org_id):
            return type("O", (), {"id": org_id, "is_active": True})()

    return type(
        "Bundle",
        (),
        {
            "insight": repo,
            "staff": _NoStaff(),
            "consultants": _NoConsultant(),
            "organizations": _OrgRepo(),
        },
    )()


def _member(user_id: str, organization_id: str) -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email=f"{user_id[:8]}@example.test",
        role="member",
        organization_id=organization_id,
        is_org_member=True,
    )


@pytest.fixture()
def api():
    repo = InMemoryInsightRepository()
    app = FastAPI()
    app.include_router(v3_insight.router)
    state = {"user": _member(ALICE, ORG_A), "unauthenticated": False}

    async def _current_user():
        if state["unauthenticated"]:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return state["user"]

    async def _repositories():
        return _bundle(repo)

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_repositories] = _repositories
    return SimpleNamespace(client=TestClient(app), repo=repo, state=state)


def _create(api, title="Scope 1 questions"):
    response = api.client.post(
        f"{BASE}/conversations", json={"organization_id": ORG_A, "title": title}
    )
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------------------
# Persistence surface
# --------------------------------------------------------------------------
def test_create_list_and_read_conversation(api):
    created = _create(api)
    assert created["organization_id"] == ORG_A
    assert created["created_by"] == ALICE
    assert created["title"] == "Scope 1 questions"

    listed = api.client.get(f"{BASE}/conversations", params={"organization_id": ORG_A})
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert [c["id"] for c in body["conversations"]] == [created["id"]]
    assert body["total"] == 1

    read = api.client.get(
        f"{BASE}/conversations/{created['id']}", params={"organization_id": ORG_A}
    )
    assert read.status_code == 200, read.text
    assert read.json()["id"] == created["id"]


def test_messages_persist_in_ordinal_order(api):
    conversation = _create(api)
    for text in ("What were my Scope 1 emissions in January 2024?", "Show the evidence."):
        response = api.client.post(
            f"{BASE}/conversations/{conversation['id']}/messages",
            json={"organization_id": ORG_A, "content": text},
        )
        assert response.status_code == 201, response.text

    third = api.client.post(
        f"{BASE}/conversations/{conversation['id']}/messages",
        json={"organization_id": ORG_A, "content": "third"},
    ).json()
    assert third["ordinal"] == 3

    listed = api.client.get(
        f"{BASE}/conversations/{conversation['id']}/messages",
        params={"organization_id": ORG_A},
    )
    assert listed.status_code == 200, listed.text
    messages = listed.json()["messages"]
    assert [m["ordinal"] for m in messages] == [1, 2, 3]
    assert [m["role"] for m in messages] == ["user", "user", "user"]
    assert messages[0]["content"].startswith("What were my Scope 1 emissions")


def test_blank_content_is_rejected(api):
    conversation = _create(api)
    response = api.client.post(
        f"{BASE}/conversations/{conversation['id']}/messages",
        json={"organization_id": ORG_A, "content": "   "},
    )
    assert response.status_code == 422
    assert api.repo.writes == 1  # only the conversation was written


# --------------------------------------------------------------------------
# Creator-private visibility (D2 §9.2)
# --------------------------------------------------------------------------
def test_same_organization_other_principal_cannot_read_or_list(api):
    conversation = _create(api)
    api.state["user"] = _member(BOB, ORG_A)

    listed = api.client.get(f"{BASE}/conversations", params={"organization_id": ORG_A})
    assert listed.json()["conversations"] == []
    assert listed.json()["total"] == 0

    read = api.client.get(
        f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
    )
    assert read.status_code == 404

    messages = api.client.get(
        f"{BASE}/conversations/{conversation['id']}/messages",
        params={"organization_id": ORG_A},
    )
    assert messages.status_code == 404


def test_other_principal_cannot_append_to_someone_elses_conversation(api):
    conversation = _create(api)
    api.state["user"] = _member(BOB, ORG_A)
    writes_before = api.repo.writes

    response = api.client.post(
        f"{BASE}/conversations/{conversation['id']}/messages",
        json={"organization_id": ORG_A, "content": "injected"},
    )
    assert response.status_code == 404
    assert api.repo.writes == writes_before
    assert api.repo.messages.get(conversation["id"]) in (None, [])


# --------------------------------------------------------------------------
# Organisation isolation (D2 §8.4 — a stored id is not a grant)
# --------------------------------------------------------------------------
def test_cross_organization_read_and_write_are_denied(api):
    conversation = _create(api)  # ORG_A / ALICE

    # An ORG_B member holding the exact conversation id: the organisation-scoped
    # read finds nothing, and their own organisation cannot be used as a key.
    api.state["user"] = _member(BOB, ORG_B)
    read = api.client.get(
        f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_B}
    )
    assert read.status_code == 404

    # Naming the other organisation is refused outright by ensure_org_access.
    writes_before = api.repo.writes
    assert (
        api.client.get(
            f"{BASE}/conversations/{conversation['id']}", params={"organization_id": ORG_A}
        ).status_code
        == 403
    )
    assert (
        api.client.post(
            f"{BASE}/conversations/{conversation['id']}/messages",
            json={"organization_id": ORG_A, "content": "cross-tenant"},
        ).status_code
        == 403
    )
    assert (
        api.client.post(
            f"{BASE}/conversations", json={"organization_id": ORG_A, "title": "cross-tenant"}
        ).status_code
        == 403
    )
    assert api.repo.writes == writes_before


def test_authentication_is_required(api):
    api.state["unauthenticated"] = True
    assert (
        api.client.get(f"{BASE}/conversations", params={"organization_id": ORG_A}).status_code
        == 401
    )
    assert (
        api.client.post(
            f"{BASE}/conversations", json={"organization_id": ORG_A, "title": "nope"}
        ).status_code
        == 401
    )


def test_insight_authored_messages_cannot_be_persisted_in_i1(api):
    """No LLM exists in I1: CarbonTally-authored content must not be creatable."""
    conversation = _create(api)
    writes_before = api.repo.writes
    response = api.client.post(
        f"{BASE}/conversations/{conversation['id']}/messages",
        json={"organization_id": ORG_A, "content": "fabricated", "role": "insight"},
    )
    assert response.status_code == 422
    assert api.repo.writes == writes_before
