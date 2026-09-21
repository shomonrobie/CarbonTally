"""CarbonTally Insight — I1 domain entities (persistent conversation foundation).

Authorisation: CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002 (I1 only).

Ratified authority: `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`
(D2) §5.1 (conversations are persisted), §6 (separate conversational domain —
never the human messaging tables), §7 (three-layer model; **I1 builds Layer 1
only**), §3.2.1/§3.8 (canonical `carbontally_insight_*` naming for all new
implementation), §9.2 (initial creator-private visibility), §8 (every read
re-authorised; stored references are not grants).

Scope discipline (D2 §23.2/§24.2/§24.5, prompt §7):

* These entities carry only the **minimum technical fields** required to persist
  and retrieve Layer-1 conversations and messages.
* NO product status vocabulary (D2 §11.6 defers the exact answer-state
  vocabulary), NO retention/archival/deletion semantics (I7, D2 §20), NO
  billing/allowance fields (I8, D2 §21), NO AI interaction/audit fields
  (Layer 2/3 = I4, D2 §7.1/§22), NO model/provider fields (I8, prompt §3/§12).
* `role` is the author kind of a persisted message (a conversation cannot be
  represented without it). `user` = a human-authored message; `insight` = a
  CarbonTally Insight-authored message. It is deliberately NOT an answer status.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

#: Author kinds persisted by I1. Deliberately minimal (see module docstring).
MESSAGE_ROLES = ("user", "insight")


@dataclass
class InsightConversation:
    """One CarbonTally Insight conversation (Layer 1 conversation history)."""

    id: str
    organization_id: str
    created_by: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class InsightMessage:
    """One persisted message inside an Insight conversation."""

    id: str
    conversation_id: str
    organization_id: str
    created_by: Optional[str]
    role: str
    content: str
    ordinal: int
    created_at: datetime
