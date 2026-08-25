"""Consultant-client messaging repository (D27 / D19 §16).

Service-role persistence over the existing Supabase Realtime messaging tables
(``conversations`` / ``messages`` / ``conversation_participants``). Every write
is authorized by the API before reaching this repository:

* participants: org members of the conversation org + consultant firm members
  holding an ACTIVE consultant-client grant (D15) for the org;
* Processing Entity staff are structurally excluded (the API never passes an
  entity-staff caller and RLS has no entity storey).
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.messaging import Conversation, ConversationParticipant, Message

_CONVERSATION_COLUMNS = (
    "id, organization_id, subject, status, created_by, created_at, updated_at, "
    "last_message_at"
)
_PARTICIPANT_COLUMNS = (
    "id, conversation_id, user_id, is_active, joined_at, last_read_at, metadata"
)
_MESSAGE_COLUMNS = (
    "id, conversation_id, sender_id, organization_id, content, is_read, "
    "parent_message_id, sent_at, created_at"
)


def _row_to_conversation(row: Any) -> Conversation:
    r = dict(row)
    return Conversation(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else None,
        subject=r.get("subject"),
        status=str(r.get("status") or "open"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
        last_message_at=r.get("last_message_at"),
    )


def _row_to_participant(row: Any) -> ConversationParticipant:
    r = dict(row)
    return ConversationParticipant(
        id=str(r["id"]),
        conversation_id=str(r["conversation_id"]),
        user_id=str(r["user_id"]),
        is_active=bool(r.get("is_active", True)),
        joined_at=r.get("joined_at"),
        last_read_at=r.get("last_read_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


def _row_to_message(row: Any) -> Message:
    r = dict(row)
    return Message(
        id=str(r["id"]),
        conversation_id=str(r["conversation_id"]),
        sender_id=str(r["sender_id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else None,
        content=str(r["content"]),
        is_read=bool(r.get("is_read", False)),
        parent_message_id=str(r["parent_message_id"]) if r.get("parent_message_id") else None,
        sent_at=r.get("sent_at"),
        created_at=r.get("created_at"),
    )


class MessagingRepository(AbstractRepository[Conversation]):
    """Service-role persistence for the Realtime messaging tables."""

    # -- conversations -------------------------------------------------------
    async def get(self, conversation_id: str) -> Optional[Conversation]:
        row = await self._fetch_one(
            f"SELECT {_CONVERSATION_COLUMNS} FROM public.conversations "
            "WHERE id = $1",
            conversation_id,
        )
        return _row_to_conversation(row) if row is not None else None

    async def create_conversation(
        self,
        *,
        organization_id: str,
        subject: str,
        created_by: str,
    ) -> Conversation:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.conversations (
                organization_id, subject, status, created_by, created_at, updated_at
            ) VALUES ($1, $2, 'open', $3, NOW(), NOW())
            RETURNING {_CONVERSATION_COLUMNS}
            """,
            organization_id,
            subject,
            created_by,
        )
        if row is None:
            raise RuntimeError("conversations insert returned no row")
        return _row_to_conversation(row)

    async def list_conversations_for_org(
        self, organization_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Conversation]:
        rows = await self._fetch_all(
            f"""
            SELECT {_CONVERSATION_COLUMNS} FROM public.conversations
             WHERE organization_id = $1
             ORDER BY COALESCE(last_message_at, created_at) DESC
             LIMIT {int(limit)} OFFSET {int(offset)}
            """,
            organization_id,
        )
        return [_row_to_conversation(r) for r in rows]

    async def count_conversations_for_org(self, organization_id: str) -> int:
        row = await self._fetch_one(
            "SELECT COUNT(*) FROM public.conversations WHERE organization_id = $1",
            organization_id,
        )
        return int(row[0]) if row is not None else 0

    async def close_conversation(
        self, conversation_id: str, *, closed_by: str
    ) -> bool:
        row = await self._fetch_one(
            "UPDATE public.conversations SET status = 'closed', closed_by = $2, "
            "closed_at = NOW(), updated_at = NOW() WHERE id = $1 "
            "RETURNING id",
            conversation_id,
            closed_by,
        )
        return row is not None

    # -- participants --------------------------------------------------------
    async def add_participant(
        self,
        *,
        conversation_id: str,
        user_id: str,
        metadata: Optional[dict] = None,
    ) -> ConversationParticipant:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.conversation_participants (
                conversation_id, user_id, is_active, metadata, created_at, updated_at
            ) VALUES ($1, $2, TRUE, $3, NOW(), NOW())
            ON CONFLICT (conversation_id, user_id) DO UPDATE
                SET is_active = TRUE, updated_at = NOW()
            RETURNING {_PARTICIPANT_COLUMNS}
            """,
            conversation_id,
            user_id,
            dumps_jsonb(metadata or {}),
        )
        if row is None:
            raise RuntimeError("conversation_participants insert returned no row")
        return _row_to_participant(row)

    async def list_participants(
        self, conversation_id: str
    ) -> list[ConversationParticipant]:
        rows = await self._fetch_all(
            f"SELECT {_PARTICIPANT_COLUMNS} FROM public.conversation_participants "
            "WHERE conversation_id = $1 AND is_active = TRUE ORDER BY joined_at",
            conversation_id,
        )
        return [_row_to_participant(r) for r in rows]

    async def set_participant_active(
        self, conversation_id: str, user_id: str, is_active: bool
    ) -> bool:
        row = await self._fetch_one(
            "UPDATE public.conversation_participants SET is_active = $3, "
            "updated_at = NOW() WHERE conversation_id = $1 AND user_id = $2 "
            "RETURNING id",
            conversation_id,
            user_id,
            is_active,
        )
        return row is not None

    # -- messages ------------------------------------------------------------
    async def send_message(
        self,
        *,
        conversation_id: str,
        sender_id: str,
        organization_id: str,
        content: str,
    ) -> Message:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.messages (
                conversation_id, sender_id, organization_id, content,
                is_read, created_at
            ) VALUES ($1, $2, $3, $4, FALSE, NOW())
            RETURNING {_MESSAGE_COLUMNS}
            """,
            conversation_id,
            sender_id,
            organization_id,
            content,
        )
        if row is None:
            raise RuntimeError("messages insert returned no row")
        await self._touch_conversation(conversation_id)
        return _row_to_message(row)

    async def list_messages(
        self, conversation_id: str, *, limit: int = 200, offset: int = 0
    ) -> list[Message]:
        rows = await self._fetch_all(
            f"""
            SELECT {_MESSAGE_COLUMNS} FROM public.messages
             WHERE conversation_id = $1
             ORDER BY created_at ASC
             LIMIT {int(limit)} OFFSET {int(offset)}
            """,
            conversation_id,
        )
        return [_row_to_message(r) for r in rows]

    async def count_messages(self, conversation_id: str) -> int:
        row = await self._fetch_one(
            "SELECT COUNT(*) FROM public.messages WHERE conversation_id = $1",
            conversation_id,
        )
        return int(row[0]) if row is not None else 0

    async def mark_conversation_read(
        self, conversation_id: str, user_id: str
    ) -> bool:
        row = await self._fetch_one(
            "UPDATE public.messages SET is_read = TRUE "
            "WHERE conversation_id = $1 AND sender_id != $2 "
            "RETURNING id",
            conversation_id,
            user_id,
        )
        await self._fetch_one(
            "UPDATE public.conversation_participants SET last_read_at = NOW(), "
            "updated_at = NOW() WHERE conversation_id = $1 AND user_id = $2 "
            "RETURNING id",
            conversation_id,
            user_id,
        )
        return row is not None

    async def _touch_conversation(self, conversation_id: str) -> None:
        await self._execute(
            "UPDATE public.conversations SET last_message_at = NOW(), "
            "updated_at = NOW() WHERE id = $1",
            conversation_id,
        )

    async def save(self, entity: Conversation) -> Conversation:
        return entity

    async def delete(self, id: str) -> None:  # noqa: A002 — abstract contract
        return None
