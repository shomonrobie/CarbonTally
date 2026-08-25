"""Consultant-client messaging domain (D27 / D19 §16).

Consultant ↔ client messaging through CarbonTally uses the existing Supabase
Realtime messaging tables (``conversations`` / ``messages`` /
``conversation_participants``). Authorization is enforced by the API and RLS:

* org members of the conversation's organisation participate;
* consultants participate only through an ACTIVE consultant-client grant (D15)
  for that organisation;
* Processing Entity staff NEVER participate (D18 boundary) — the API and the
  RLS storey (no entity policy) both deny them.

This module is the pure domain model (immutable dataclasses); it never
authorizes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

#: Conversation statuses (presentation only — the conversation row's authority
#: comes from participation + org/consultant RLS).
CONVERSATION_STATUSES: tuple[str, ...] = ("open", "closed")


@dataclass(frozen=True, slots=True)
class ConversationParticipant:
    """A participant on a conversation (``conversation_participants``)."""

    id: str
    conversation_id: str
    user_id: str
    is_active: bool = True
    joined_at: Optional[datetime] = None
    last_read_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Conversation:
    """A conversation thread (``conversations``)."""

    id: str
    organization_id: Optional[str] = None
    subject: Optional[str] = None
    status: str = "open"
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    participants: list = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Message:
    """A message within a conversation (``messages``)."""

    id: str
    conversation_id: str
    sender_id: str
    organization_id: Optional[str] = None
    content: str = ""
    is_read: bool = False
    parent_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
