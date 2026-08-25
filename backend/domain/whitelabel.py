"""White-label domain: custom domains + custom email senders (D27 / D19 §11-13).

CarbonTally provides white-label access to its platform; the consultant owns
the domain/registrar/DNS/email infrastructure. CarbonTally provides the
platform, branding, custom-domain integration, verification and authorized
presentation context.

This module is the pure domain model for the two lifecycle carriers:
``consultant_custom_domains`` (PENDING/VERIFIED/ACTIVE/REMOVED_SUSPENDED) and
``consultant_senders`` (PENDING/VERIFIED/REMOVED).

Critical rule (D19 §12): a domain NEVER grants authorization. The server always
resolves the brand from the authenticated consultant relationship; the domain
only selects which authorized brand is presented (Vercel forwards the origin,
authentication/authorization stay authoritative). Custom senders are verified
through Resend's domain verification; only VERIFIED senders may be used as a
From address (unverified sender → DENIED; arbitrary From addresses are never
allowed).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

#: Custom-domain lifecycle (D19 §12).
DOMAIN_STATUSES: tuple[str, ...] = (
    "pending", "verified", "active", "removed_suspended",
)

#: Sender lifecycle (D19 §13).
SENDER_STATUSES: tuple[str, ...] = ("pending", "verified", "removed")


@dataclass(frozen=True, slots=True)
class CustomDomain:
    """A consultant custom portal domain (``consultant_custom_domains``)."""

    id: str
    consultant_id: str
    domain: str
    status: str = "pending"
    verification_token: str = ""
    verified_at: Optional[datetime] = None
    removed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class CustomSender:
    """A consultant custom email sender (``consultant_senders``)."""

    id: str
    consultant_id: str
    email: str
    domain: Optional[str] = None
    status: str = "pending"
    verification_token: str = ""
    verified_at: Optional[datetime] = None
    removed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
