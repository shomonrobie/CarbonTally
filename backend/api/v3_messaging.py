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


# ---------------------------------------------------------------------------
# Phase 5 / WS2 (D39) — PE <-> CarbonTally Operations operational messaging
# (PE-MSG-001). Same conversation family; conversation_kind='entity' rows.
# ---------------------------------------------------------------------------
import logging  # noqa: E402
import uuid  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

from domain.audit import AuditEntry  # noqa: E402


class EntityConversationCreate(BaseModel):
    processing_entity_id: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=300)
    context: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")


async def _resolve_entity_actor(
    repos: RepositoryBundle, current_user: AuthUser
):
    """Return (domain, entity_id): ('pe', entity) for active PE members,
    ('ops', None) for authorised CarbonTally Operations, else 403."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorised for PE operational messaging")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(status_code=403, detail="Not authorised for PE operational messaging")
    if context.profile.entity_id is not None:
        entity_id = context.profile.entity_id
        entity = await repos.entities.get(entity_id)
        if entity is None or entity.status != "active":
            raise HTTPException(status_code=403, detail="Processing entity is not active")
        return "pe", entity_id
    # CarbonTally internal staff must hold the support permission (same gate as
    # N1 org-support messaging) to join PE operational conversations.
    try:
        ensure_staff_permission(context, "can_manage_staff")
        return "ops", None
    except HTTPException as exc:
        raise HTTPException(status_code=403, detail="Operations support permission required") from exc


async def _entity_conv_read_access(
    repos: RepositoryBundle, current_user: AuthUser, conversation: dict
):
    """Authorize access to one entity conversation; returns actor domain."""
    if conversation is None or conversation.get("conversation_kind") != "entity":
        raise HTTPException(status_code=404, detail="conversation not found")
    entity_id = conversation.get("processing_entity_id")
    if not entity_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    domain, actor_entity = await _resolve_entity_actor(repos, current_user)
    if domain == "pe" and actor_entity != entity_id:
        raise HTTPException(status_code=403, detail="Not a member of this processing entity's conversation")
    return domain


async def _validate_entity_context(repos, entity_id: str, context: Optional[dict]):
    """Entity conversations may carry batch/item work context ONLY when the
    entity is the assigned processor. Returns normalized context."""
    if context is None:
        return None
    ctx_type = context.get("type")
    ctx_id = context.get("id")
    if ctx_type not in ("batch", "item") or not ctx_id:
        raise HTTPException(status_code=422, detail="context.type must be 'batch' or 'item' with a context.id")
    if ctx_type == "batch":
        batch = await repos.manual_extraction.get_batch(ctx_id)
        if batch is None:
            raise HTTPException(status_code=422, detail="context batch not found")
        if str(batch.entity_id or "") != entity_id:
            raise HTTPException(status_code=403, detail="Context batch is not assigned to this processing entity")
        return {"type": "batch", "id": ctx_id}
    item = await repos.manual_extraction.get_item(ctx_id)
    if item is None:
        raise HTTPException(status_code=422, detail="context item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None or str(batch.entity_id or "") != entity_id:
        raise HTTPException(status_code=403, detail="Context item is not assigned to this processing entity")
    return {"type": "item", "id": ctx_id}


async def _audit_entity(repos, *, conversation_id, action, actor, details):
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=conversation_id,
            entity_type="conversation",
            entity_id=conversation_id,
            action=action,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields=details,
            ip_address=None,
        )
    )


async def _entity_conversation_rows(repos, rows):
    out = []
    for conv in rows:
        participants = await repos.messaging.list_participants(conv["id"])
        out.append({
            **conv,
            "participant_count": len(participants),
            "message_count": await repos.messaging.count_messages(conv["id"]),
        })
    return out


@router.get("/entity-conversations")
async def list_entity_conversations(
    entity_id: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List PE operational conversations (own entity for PE members; all or
    filtered for authorised Operations)."""
    domain, actor_entity = await _resolve_entity_actor(repos, current_user)
    scope = actor_entity if domain == "pe" else (entity_id or None)
    rows = await repos.messaging.list_entity_conversations(scope)
    return {"conversations": await _entity_conversation_rows(repos, rows),
            "total": len(rows), "scope": scope}


@router.post("/entity-conversations", status_code=201)
async def create_entity_conversation(
    payload: EntityConversationCreate,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create a PE operational conversation. For PE members the entity is their
    own ACTIVE entity (client-supplied entity ids are never trusted for PE
    callers). Authorised Operations may open one for any active entity."""
    domain, actor_entity = await _resolve_entity_actor(repos, current_user)
    if domain == "pe":
        entity_id = actor_entity
    else:
        if not payload.processing_entity_id:
            raise HTTPException(status_code=422, detail="processing_entity_id is required for Operations")
        entity = await repos.entities.get(payload.processing_entity_id)
        if entity is None or entity.status != "active":
            raise HTTPException(status_code=422, detail="processing entity not found or not active")
        entity_id = payload.processing_entity_id
    context = await _validate_entity_context(repos, entity_id, payload.context)
    conv = await repos.messaging.create_entity_conversation(
        processing_entity_id=entity_id,
        subject=payload.subject.strip(),
        created_by=current_user.user_id,
        context=context,
    )
    await repos.messaging.ensure_participant(conv["id"], current_user.user_id)
    await _audit_entity(repos, conversation_id=conv["id"], action="pe_msg:conversation_created",
                        actor=current_user.user_id,
                        details={"processing_entity_id": entity_id,
                                 "subject": conv["subject"], "context": context,
                                 "actor_domain": domain})
    return {"conversation": conv}


@router.get("/entity-conversations/{conversation_id}/messages")
async def list_entity_messages(
    conversation_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    conv = await repos.messaging.get_entity_conversation(conversation_id)
    await _entity_conv_read_access(repos, current_user, conv)
    await repos.messaging.ensure_participant(conversation_id, current_user.user_id)
    messages = await repos.messaging.list_messages(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [
            {"id": m.id, "sender_id": m.sender_id, "content": m.content,
             "is_read": m.is_read, "created_at": m.created_at}
            for m in messages
        ],
        "total": await repos.messaging.count_messages(conversation_id),
    }


@router.post("/entity-conversations/{conversation_id}/messages", status_code=201)
async def send_entity_message(
    conversation_id: str,
    payload: MessageSend,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    conv = await repos.messaging.get_entity_conversation(conversation_id)
    domain = await _entity_conv_read_access(repos, current_user, conv)
    await repos.messaging.ensure_participant(conversation_id, current_user.user_id)
    message = await repos.messaging.send_message(
        conversation_id=conversation_id,
        sender_id=current_user.user_id,
        organization_id=None,
        content=payload.content.strip(),
    )
    await _audit_entity(repos, conversation_id=conversation_id, action="pe_msg:message_sent",
                        actor=current_user.user_id,
                        details={"sender": current_user.user_id, "actor_domain": domain,
                                 "message_id": message.id})
    # D40 — notify the opposite side (server-resolved recipients only).
    entity_id = conv.get("processing_entity_id")
    try:
        if domain == "pe":
            recipients = await repos.notifications.support_staff_user_ids()
            ntype, title, link = "pe_msg.message",                 "PE operational message received", "/ops"
        else:
            recipients = await repos.notifications.entity_participant_user_ids(
                conversation_id, entity_id, exclude_user=current_user.user_id)
            ntype, title, link = "pe_msg.ops_reply",                 "Operations response received", "/pe"
        for recipient in recipients:
            await repos.notifications.create_idempotent(
                recipient,
                f"pe_msg:{message.id}:{recipient}",
                notification_type=ntype,
                title=title,
                message="A PE operational conversation was updated",
                priority=40,
                link=link,
                actor_domain=domain,
            )
    except Exception:  # best effort; business action already committed
        logging.getLogger("carbon_tally.pe_msg").warning(
            "notification producer failed for conversation %s", conversation_id)
    return {"message": {"id": message.id, "conversation_id": message.conversation_id,
                         "sender_id": message.sender_id, "content": message.content,
                         "created_at": message.created_at}}


@router.post("/entity-conversations/{conversation_id}/read")
async def mark_entity_conversation_read(
    conversation_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    conv = await repos.messaging.get_entity_conversation(conversation_id)
    await _entity_conv_read_access(repos, current_user, conv)
    await repos.messaging.ensure_participant(conversation_id, current_user.user_id)
    await repos.messaging.mark_conversation_read(conversation_id, current_user.user_id)
    return {"success": True}
