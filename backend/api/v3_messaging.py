"""V3 consultant-client messaging (D27 / D19 §16) + N1 support messaging.

Authorization:

* participants: org members of the conversation's organisation, plus
  consultant firm members holding an ACTIVE consultant-client grant (D15) for
  the organisation;
* N1 — CarbonTally Support / Authorised Admin: INTERNAL staff (entity_id IS
  NULL) holding the staff-admin permission (``can_manage_staff``) may message
  authorised organisations as a ``staff`` participant. General employees and
  Processing Entity staff never get messaging access (entity staff are neither
  org members nor consultants; RLS has no entity messaging storey) — the D18
  boundary is absolute (D19 §17).

Realtime: the API persists rows through the service role; the frontend
subscribes with ``postgres_changes`` (Supabase Realtime) for live updates.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
    require_org_member,
)
from auth import AuthUser, get_current_user
from api.consultant_auth import ensure_consultant_org_access
from api.operations_auth import _resolve_context, ensure_staff_permission

router = APIRouter(prefix="/api/v3/messaging", tags=["V3 — Messaging (D19)"])


class ConversationCreate(BaseModel):
    organization_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=300)

    model_config = ConfigDict(extra="forbid")


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)

    model_config = ConfigDict(extra="forbid")


async def _authorize_org_actor(
    repos: RepositoryBundle, current_user: AuthUser, organization_id: str
) -> str:
    """Authorize the caller for messaging in ``organization_id``.

    Returns the caller's participant role: ``org_member``, ``consultant`` or
    ``staff``. Raises 403 for anyone else (including Processing Entity staff
    and general CarbonTally employees).

    N1 — staff path: only INTERNAL CarbonTally staff (``entity_id IS NULL``)
    holding the staff-admin permission (``can_manage_staff``) may message an
    organisation. This is the "CarbonTally Support / Authorised Admin" gate;
    the permission is resolved from the authoritative ``staff_roles`` catalog,
    never from a client claim.
    """
    # Org members (customer workspace) may message their own org.
    if current_user.is_org_member and getattr(current_user, "organization_id", None) == organization_id:
        return "org_member"
    # Consultants with an ACTIVE grant for the org may message the client.
    try:
        await ensure_consultant_org_access(current_user, repos, organization_id)
        return "consultant"
    except HTTPException:
        pass
    # N1 — CarbonTally support/admin (internal staff, staff-admin permission).
    if current_user.is_staff:
        context = await _resolve_context(current_user, repos)
        if context is not None and context.profile.entity_id is None:
            try:
                ensure_staff_permission(context, "can_manage_staff")
                return "staff"
            except HTTPException:
                pass
    raise HTTPException(
        status_code=403,
        detail=(
            "Messaging requires an active membership in the organisation, an "
            "active consultant-client grant, or CarbonTally support/admin "
            "authority (N1)"
        ),
    )


@router.post("/conversations", status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create a conversation thread for the organisation.

    Both org members and active-grant consultants may create threads; the
    creator is added as the first participant. Entity staff are denied.
    """
    role = await _authorize_org_actor(repos, current_user, payload.organization_id)
    conversation = await repos.messaging.create_conversation(
        organization_id=payload.organization_id,
        subject=payload.subject.strip(),
        created_by=current_user.user_id,
    )
    await repos.messaging.add_participant(
        conversation_id=conversation.id,
        user_id=current_user.user_id,
        metadata={"participant_role": role},
    )
    return {
        "conversation": {
            "id": conversation.id,
            "organization_id": conversation.organization_id,
            "subject": conversation.subject,
            "status": conversation.status,
            "created_by": conversation.created_by,
            "created_at": conversation.created_at,
        }
    }


@router.get("/conversations")
async def list_conversations(
    organization_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the organisation's conversations (org member or active-grant
    consultant only)."""
    await _authorize_org_actor(repos, current_user, organization_id)
    conversations = await repos.messaging.list_conversations_for_org(organization_id)
    out = []
    for conv in conversations:
        participants = await repos.messaging.list_participants(conv.id)
        out.append(
            {
                "id": conv.id,
                "organization_id": conv.organization_id,
                "subject": conv.subject,
                "status": conv.status,
                "created_at": conv.created_at,
                "last_message_at": conv.last_message_at,
                "participant_count": len(participants),
                "message_count": await repos.messaging.count_messages(conv.id),
            }
        )
    return {"conversations": out, "total": len(out)}


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List messages in a conversation (participant-scoped)."""
    conversation = await repos.messaging.get(conversation_id)
    if conversation is None or not conversation.organization_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    await _authorize_org_actor(repos, current_user, conversation.organization_id)
    messages = await repos.messaging.list_messages(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "content": m.content,
                "is_read": m.is_read,
                "created_at": m.created_at,
            }
            for m in messages
        ],
        "total": await repos.messaging.count_messages(conversation_id),
    }


@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def send_message(
    conversation_id: str,
    payload: MessageSend,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Send a message into a conversation (authorized participant)."""
    conversation = await repos.messaging.get(conversation_id)
    if conversation is None or not conversation.organization_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    await _authorize_org_actor(repos, current_user, conversation.organization_id)
    message = await repos.messaging.send_message(
        conversation_id=conversation_id,
        sender_id=current_user.user_id,
        organization_id=conversation.organization_id,
        content=payload.content.strip(),
    )
    return {
        "message": {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "created_at": message.created_at,
        }
    }


@router.post("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Mark the conversation read by the caller."""
    conversation = await repos.messaging.get(conversation_id)
    if conversation is None or not conversation.organization_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    await _authorize_org_actor(repos, current_user, conversation.organization_id)
    await repos.messaging.mark_conversation_read(conversation_id, current_user.user_id)
    return {"success": True}
