"""CarbonTally Insight — I1 persistence API (Layer 1 only).

Authorisation: CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.

Ratified authority — D2 (§5.1 persisted conversations, §6 separate domain, §7
Layer 1 at I1, §8 authorization, §9.2 creator-private visibility, §24.2 the I1
MAY-include list, §24.3/§24.4 boundaries).

This surface is deliberately **persistence only**: create / list / read
conversations, append a message, list a conversation's messages. It does **not**
answer questions, invoke any LLM, expose tools, retrieve evidence, summarise
reports, or write AI-interaction/audit rows (I3–I8).

Authorization on every endpoint (§8.1/§8.4/§9.2):

1. the caller must be an authenticated organisation member
   (``require_org_member``);
2. ``ensure_org_access`` re-checks the organisation per request, so a stored id
   or reference never confers access;
3. **creator-private**: a conversation is returned only to the principal that
   created it. Internal-staff Insight visibility is DEFERRED by D2 §10.2, so I1
   grants no staff exception — every caller is creator-scoped;
4. a conversation outside the caller's organisation, or created by another
   principal, is reported as ``404`` (existence is not disclosed).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import RepositoryBundle, get_repositories
from api.insight_authz import (
    InsightAccess,
    authorize_insight_scope,
    conversation_is_visible,
    require_insight_user,
    visibility_created_by,
)
from auth import AuthUser

router = APIRouter(
    prefix="/api/v3/insight",
    tags=["V3 — CarbonTally Insight"],
    # I2 (D2 §8.5): authenticated, non-PE principals only, attached to the router
    # so every present and future Insight route is deny-by-default by
    # construction. The organization scope is resolved per request by
    # `authorize_insight_scope` (customer membership / consultant grant /
    # internal staff profile).
    dependencies=[Depends(require_insight_user)],
)

#: I1 persists human-authored messages only. ``insight`` is a reserved author
#: kind for the later authorized LLM stage; accepting it here would let a caller
#: fabricate CarbonTally-authored content, so it is refused.
_CLIENT_ROLE = "user"

_MAX_TITLE_LENGTH = 200
_MAX_CONTENT_LENGTH = 20000


class ConversationCreateIn(BaseModel):
    organization_id: str = Field(..., min_length=1)
    title: Optional[str] = Field(default=None, max_length=_MAX_TITLE_LENGTH)


class MessageCreateIn(BaseModel):
    organization_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=_MAX_CONTENT_LENGTH)
    role: str = Field(default=_CLIENT_ROLE)


def _conversation_out(conversation) -> dict:
    return {
        "id": conversation.id,
        "organization_id": conversation.organization_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "created_by": conversation.created_by,
    }


def _message_out(message) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "organization_id": message.organization_id,
        "role": message.role,
        "content": message.content,
        "ordinal": message.ordinal,
        "created_at": message.created_at.isoformat(),
    }


async def _authorised_conversation(
    repos: RepositoryBundle,
    access: InsightAccess,
    conversation_id: str,
):
    """Resolve a conversation for the authorized caller or raise 404.

    I2 applies both ratified boundaries through the single visibility model
    (D2 §9.2/§9.6): the authorized organization **and** creator identity. The
    conversation is re-resolved from the database on every read, so a stored id
    or an earlier decision is never a grant (D2 §8.4/§8.8) and existence is not
    disclosed.
    """
    conversation = await repos.insight.get_conversation(
        conversation_id=conversation_id, organization_id=access.organization_id
    )
    if not conversation_is_visible(access, conversation):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateIn,
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create a persisted CarbonTally Insight conversation (creator-private)."""
    access = await authorize_insight_scope(
        current_user, repos, payload.organization_id
    )
    conversation = await repos.insight.create_conversation(
        organization_id=access.organization_id,
        created_by=access.user_id,
        title=payload.title,
    )
    return _conversation_out(conversation)


@router.get("/conversations")
async def list_conversations(
    organization_id: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the caller's own conversations in one authorised organisation."""
    access = await authorize_insight_scope(current_user, repos, organization_id)
    conversations = await repos.insight.list_conversations(
        organization_id=access.organization_id,
        created_by=visibility_created_by(access),
        limit=limit,
        offset=offset,
    )
    total = await repos.insight.count_conversations(
        organization_id=access.organization_id,
        created_by=visibility_created_by(access),
    )
    return {
        "conversations": [_conversation_out(c) for c in conversations],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    organization_id: str = Query(..., min_length=1),
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Read one authorised conversation."""
    access = await authorize_insight_scope(current_user, repos, organization_id)
    conversation = await _authorised_conversation(repos, access, conversation_id)
    return _conversation_out(conversation)


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def append_message(
    conversation_id: str,
    payload: MessageCreateIn,
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Persist a human-authored message in an authorised conversation."""
    access = await authorize_insight_scope(
        current_user, repos, payload.organization_id
    )
    if payload.role != _CLIENT_ROLE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Only human-authored messages may be persisted in I1; "
                "CarbonTally Insight-authored messages belong to a later authorized stage."
            ),
        )
    conversation = await _authorised_conversation(repos, access, conversation_id)
    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="content must not be blank",
        )
    message = await repos.insight.add_message(
        conversation_id=conversation.id,
        organization_id=conversation.organization_id,
        created_by=access.user_id,
        role=_CLIENT_ROLE,
        content=content,
    )
    return _message_out(message)


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    organization_id: str = Query(..., min_length=1),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_insight_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the persisted messages of an authorised conversation (ordinal order)."""
    access = await authorize_insight_scope(current_user, repos, organization_id)
    conversation = await _authorised_conversation(repos, access, conversation_id)
    messages = await repos.insight.list_messages(
        conversation_id=conversation.id,
        organization_id=conversation.organization_id,
        limit=limit,
        offset=offset,
    )
    return {
        "conversation_id": conversation.id,
        "messages": [_message_out(m) for m in messages],
        "limit": limit,
        "offset": offset,
    }
