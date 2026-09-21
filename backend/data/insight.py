"""CarbonTally Insight — I1 persistence (Layer 1 only).

Authorisation: CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002.
Ratified authority: D2 §5.1, §6, §7 (Layer 1 at I1), §8 (every read
re-authorised; stored references are not grants), §9.2 (creator-private),
§24.2 (I1 MAY-include list), §24.3/§24.5 (boundaries).

Design notes (not obvious from the DDL):

* The repository is bound to the **service-role** pool like every other
  repository, so RLS does not protect it: **every read here is explicitly
  scoped by ``organization_id``** (defence in depth with the RLS policies in
  ``20261001000000_p8_i1_insight_persistence.sql``) and the API layer
  re-authorises the principal on every request (D2 §8.1/§8.4).
* ``created_by`` is never inferred from a stored row: callers pass the
  authenticated principal, and creator-private reads take that principal as an
  explicit filter argument.
* Message ordering uses an explicit 1-based ``ordinal`` allocated inside the
  INSERT statement. ``UNIQUE (conversation_id, ordinal)`` is the authority: a
  concurrent writer for the same conversation surfaces as an IntegrityError
  rather than a silent re-order. No retry loop is added in I1 (single writer
  path: the backend).
* No LLM, tools, statuses, retention or AI-interaction rows are written here
  (I3/I4/I7/I8).
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from data.base import AbstractRepository
from domain.insight import InsightConversation, InsightMessage

_CONVERSATION_COLUMNS = "id, organization_id, created_by, title, created_at, updated_at"
_MESSAGE_COLUMNS = (
    "id, conversation_id, organization_id, created_by, role, content, ordinal, created_at"
)

_CREATE_CONVERSATION_SQL = f"""
    INSERT INTO public.carbontally_insight_conversations
        (organization_id, created_by, title)
    VALUES ($1, $2, $3)
    RETURNING {_CONVERSATION_COLUMNS}
"""

_LIST_CONVERSATIONS_SQL = f"""
    SELECT {_CONVERSATION_COLUMNS}
      FROM public.carbontally_insight_conversations
     WHERE organization_id = $1
       AND ($2::uuid IS NULL OR created_by = $2::uuid)
     ORDER BY created_at DESC, id DESC
     LIMIT $3 OFFSET $4
"""

_GET_CONVERSATION_SQL = f"""
    SELECT {_CONVERSATION_COLUMNS}
      FROM public.carbontally_insight_conversations
     WHERE id = $1 AND organization_id = $2
"""

_ADD_MESSAGE_SQL = f"""
    INSERT INTO public.carbontally_insight_messages
        (conversation_id, organization_id, created_by, role, content, ordinal)
    SELECT $1, $2, $3, $4, $5, coalesce(max(ordinal), 0) + 1
      FROM public.carbontally_insight_messages
     WHERE conversation_id = $1
    RETURNING {_MESSAGE_COLUMNS}
"""

_LIST_MESSAGES_SQL = f"""
    SELECT {_MESSAGE_COLUMNS}
      FROM public.carbontally_insight_messages
     WHERE conversation_id = $1 AND organization_id = $2
     ORDER BY ordinal ASC
     LIMIT $3 OFFSET $4
"""

_COUNT_CONVERSATIONS_SQL = """
    SELECT count(*) AS n
      FROM public.carbontally_insight_conversations
     WHERE organization_id = $1
       AND ($2::uuid IS NULL OR created_by = $2::uuid)
"""


def _row_to_conversation(row: Any) -> InsightConversation:
    r = dict(row)
    return InsightConversation(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        created_by=str(r["created_by"]),
        title=r.get("title"),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_message(row: Any) -> InsightMessage:
    r = dict(row)
    return InsightMessage(
        id=str(r["id"]),
        conversation_id=str(r["conversation_id"]),
        organization_id=str(r["organization_id"]),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        role=r["role"],
        content=r["content"],
        ordinal=int(r["ordinal"]),
        created_at=r["created_at"],
    )


class InsightRepository(AbstractRepository[InsightConversation]):
    """Persistence for the CarbonTally Insight Layer-1 domain."""

    # -- AbstractRepository contract -------------------------------------
    async def get(
        self, id: str, *, organization_id: str
    ) -> Optional[InsightConversation]:
        """Organisation-scoped conversation read (OHD F-04).

        The I1 contract exposed this read without organisation scoping. It had no
        caller, and an unscoped read on a service-role pool is a latent
        authorization bypass (D2 §8.4), so the scope is now a **required**
        keyword argument — the same shape the repository already uses for
        ``ActivityClarificationsRepository.get(id, *, organization_id=…)``.
        There is therefore no unscoped conversation read in the Insight
        repository at all.
        """
        return await self.get_conversation(
            conversation_id=id, organization_id=organization_id
        )

    async def save(self, entity: InsightConversation) -> InsightConversation:
        """Insert-or-update a conversation row (technical fields only).

        Every parameter is cast explicitly. The I1 statement used
        ``coalesce($5, $6)`` over untyped parameters, which PostgreSQL resolves
        to ``text`` and which therefore failed with ``DatatypeMismatchError``
        for a ``timestamptz`` target column (OHD F-02). The casts below follow
        the ratified I1 column types exactly (uuid / text / timestamptz) and add
        no product semantics.

        Internal/service use only: this is the repository's insert-or-update
        path. Request paths MUST create through :meth:`create_conversation`
        (organisation + creator supplied by the authorization layer).
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        row = await self._fetch_one(
            f"""
            INSERT INTO public.carbontally_insight_conversations
                (id, organization_id, created_by, title, created_at, updated_at)
            VALUES (
                $1::uuid,
                $2::uuid,
                $3::uuid,
                $4::text,
                coalesce($5::timestamptz, $6::timestamptz),
                coalesce($7::timestamptz, $6::timestamptz)
            )
            ON CONFLICT (id) DO UPDATE
                SET title = EXCLUDED.title,
                    updated_at = EXCLUDED.updated_at
            RETURNING {_CONVERSATION_COLUMNS}
            """,
            entity.id,
            entity.organization_id,
            entity.created_by,
            entity.title,
            entity.created_at,
            now,
            entity.updated_at,
        )
        return _row_to_conversation(row)  # type: ignore[arg-type]

    async def delete(self, id: str) -> None:
        """Refuse deletion: I1 defines no delete surface (D2 §20 defers
        retention/deletion semantics to I7)."""
        raise NotImplementedError(
            "CarbonTally Insight I1 has no delete surface; retention/deletion "
            "semantics are deferred to I7 (D2 §20, §24.3)."
        )

    # -- I1 surface ------------------------------------------------------
    async def create_conversation(
        self,
        *,
        organization_id: str,
        created_by: str,
        title: Optional[str] = None,
    ) -> InsightConversation:
        row = await self._fetch_one(
            _CREATE_CONVERSATION_SQL, organization_id, created_by, title
        )
        return _row_to_conversation(row)  # type: ignore[arg-type]

    async def list_conversations(
        self,
        *,
        organization_id: str,
        created_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[InsightConversation]:
        """List conversations for one organisation, newest first.

        ``created_by`` applies the ratified creator-private visibility filter
        (D2 §9.2). ``None`` is reserved for internal/service callers.
        """
        rows = await self._fetch_all(
            _LIST_CONVERSATIONS_SQL, organization_id, created_by, limit, offset
        )
        return [_row_to_conversation(r) for r in rows]

    async def get_conversation(
        self, *, conversation_id: str, organization_id: str
    ) -> Optional[InsightConversation]:
        """Organisation-scoped conversation read (the only read the API uses)."""
        row = await self._fetch_one(_GET_CONVERSATION_SQL, conversation_id, organization_id)
        return _row_to_conversation(row) if row else None

    async def add_message(
        self,
        *,
        conversation_id: str,
        organization_id: str,
        role: str,
        content: str,
        created_by: Optional[str] = None,
    ) -> InsightMessage:
        """Append one message, allocating the next ordinal atomically.

        The caller has already re-authorised the principal and resolved the
        conversation for that organisation; the composite FK keeps
        ``organization_id`` consistent with the parent conversation.
        """
        row = await self._fetch_one(
            _ADD_MESSAGE_SQL,
            conversation_id,
            organization_id,
            created_by,
            role,
            content,
        )
        await self._execute(
            "UPDATE public.carbontally_insight_conversations SET updated_at = now() WHERE id = $1",
            conversation_id,
        )
        return _row_to_message(row)  # type: ignore[arg-type]

    async def list_messages(
        self,
        *,
        conversation_id: str,
        organization_id: str,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[InsightMessage]:
        """Persisted messages of one conversation in explicit ordinal order."""
        rows = await self._fetch_all(
            _LIST_MESSAGES_SQL, conversation_id, organization_id, limit, offset
        )
        return [_row_to_message(r) for r in rows]

    async def count_conversations(
        self, *, organization_id: str, created_by: Optional[str] = None
    ) -> int:
        """Total conversations visible to the caller (creator-private aware)."""
        row = await self._fetch_one(_COUNT_CONVERSATIONS_SQL, organization_id, created_by)
        return int(row["n"]) if row else 0


__all__ = ["InsightRepository"]
