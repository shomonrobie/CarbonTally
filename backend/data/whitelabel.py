"""White-label repository: custom domains + custom email senders (D27 / D19).

Service-role persistence for ``consultant_custom_domains`` and
``consultant_senders``. The API layer enforces the authenticated consultant
relationship before any read/write; a domain or sender NEVER grants
authorization by itself.
"""
from __future__ import annotations

import secrets
from typing import Any, Optional

from data.base import AbstractRepository
from domain.whitelabel import CustomDomain, CustomSender


def generate_verification_token() -> str:
    """Cryptographically random verification token (TXT-record / link token)."""
    return secrets.token_urlsafe(24)


_DOMAIN_COLUMNS = (
    "id, consultant_id, domain, status, verification_token, verified_at, "
    "removed_at, created_at, updated_at"
)
_SENDER_COLUMNS = (
    "id, consultant_id, email, domain, status, verification_token, verified_at, "
    "removed_at, created_at, updated_at"
)


def _row_to_domain(row: Any) -> CustomDomain:
    r = dict(row)
    return CustomDomain(
        id=str(r["id"]),
        consultant_id=str(r["consultant_id"]),
        domain=str(r["domain"]),
        status=str(r.get("status") or "pending"),
        verification_token=str(r.get("verification_token") or ""),
        verified_at=r.get("verified_at"),
        removed_at=r.get("removed_at"),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )


def _row_to_sender(row: Any) -> CustomSender:
    r = dict(row)
    return CustomSender(
        id=str(r["id"]),
        consultant_id=str(r["consultant_id"]),
        email=str(r["email"]),
        domain=r.get("domain"),
        status=str(r.get("status") or "pending"),
        verification_token=str(r.get("verification_token") or ""),
        verified_at=r.get("verified_at"),
        removed_at=r.get("removed_at"),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )


class WhiteLabelRepository(AbstractRepository[CustomDomain]):
    """Service-role persistence for custom domains and senders."""

    # -- custom domains ------------------------------------------------------
    async def get(self, domain_id: str) -> Optional[CustomDomain]:
        row = await self._fetch_one(
            f"SELECT {_DOMAIN_COLUMNS} FROM public.consultant_custom_domains "
            "WHERE id = $1",
            domain_id,
        )
        return _row_to_domain(row) if row is not None else None

    async def get_domain_for_consultant(
        self, domain_id: str, consultant_id: str
    ) -> Optional[CustomDomain]:
        row = await self._fetch_one(
            f"SELECT {_DOMAIN_COLUMNS} FROM public.consultant_custom_domains "
            "WHERE id = $1 AND consultant_id = $2",
            domain_id,
            consultant_id,
        )
        return _row_to_domain(row) if row is not None else None

    async def list_domains(self, consultant_id: str) -> list[CustomDomain]:
        rows = await self._fetch_all(
            f"SELECT {_DOMAIN_COLUMNS} FROM public.consultant_custom_domains "
            "WHERE consultant_id = $1 ORDER BY created_at DESC",
            consultant_id,
        )
        return [_row_to_domain(r) for r in rows]

    async def create_domain(
        self, *, consultant_id: str, domain: str
    ) -> CustomDomain:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_custom_domains (
                consultant_id, domain, status, verification_token, created_at,
                updated_at
            ) VALUES ($1, $2, 'pending', $3, NOW(), NOW())
            RETURNING {_DOMAIN_COLUMNS}
            """,
            consultant_id,
            domain,
            generate_verification_token(),
        )
        if row is None:
            raise RuntimeError("consultant_custom_domains insert returned no row")
        return _row_to_domain(row)


    async def verify_domain(
        self, domain_id: str, consultant_id: str, *, token: str
    ) -> tuple[bool, str]:
        """Complete domain verification by matching the TXT token.

        In production the DNS TXT record is checked before this is called (or
        the token match is the confirmation of record placement); locally the
        token match completes the VERIFIED transition. The status becomes
        ``verified``; a separate activation moves it to ``active`` (D19 §12
        lifecycle). A domain NEVER grants authorization by itself.
        """
        domain = await self.get_domain_for_consultant(domain_id, consultant_id)
        if domain is None:
            return False, "domain not found"
        if domain.status == "removed_suspended":
            return False, "domain is removed/suspended"
        if not token or not secrets.compare_digest(domain.verification_token, token.strip()):
            return False, "invalid verification token"
        row = await self._fetch_one(
            "UPDATE public.consultant_custom_domains SET status = 'verified', "
            "verified_at = NOW(), updated_at = NOW() WHERE id = $1 RETURNING id",
            domain_id,
        )
        return row is not None, "verified"

    async def activate_domain(self, domain_id: str, consultant_id: str) -> bool:
        """Move a VERIFIED domain to ACTIVE (branding may present on it)."""
        row = await self._fetch_one(
            "UPDATE public.consultant_custom_domains SET status = 'active', "
            "updated_at = NOW() WHERE id = $1 AND consultant_id = $2 "
            "AND status = 'verified' RETURNING id",
            domain_id,
            consultant_id,
        )
        return row is not None

    async def remove_domain(self, domain_id: str, consultant_id: str) -> bool:
        row = await self._fetch_one(
            "UPDATE public.consultant_custom_domains SET status = "
            "'removed_suspended', removed_at = NOW(), updated_at = NOW() "
            "WHERE id = $1 AND consultant_id = $2 RETURNING id",
            domain_id,
            consultant_id,
        )
        return row is not None

    # -- custom senders ------------------------------------------------------
    async def get_sender(self, sender_id: str) -> Optional[CustomSender]:
        row = await self._fetch_one(
            f"SELECT {_SENDER_COLUMNS} FROM public.consultant_senders "
            "WHERE id = $1",
            sender_id,
        )
        return _row_to_sender(row) if row is not None else None

    async def get_sender_for_consultant(
        self, sender_id: str, consultant_id: str
    ) -> Optional[CustomSender]:
        row = await self._fetch_one(
            f"SELECT {_SENDER_COLUMNS} FROM public.consultant_senders "
            "WHERE id = $1 AND consultant_id = $2",
            sender_id,
            consultant_id,
        )
        return _row_to_sender(row) if row is not None else None

    async def list_senders(self, consultant_id: str) -> list[CustomSender]:
        rows = await self._fetch_all(
            f"SELECT {_SENDER_COLUMNS} FROM public.consultant_senders "
            "WHERE consultant_id = $1 ORDER BY created_at DESC",
            consultant_id,
        )
        return [_row_to_sender(r) for r in rows]

    async def create_sender(
        self, *, consultant_id: str, email: str
    ) -> CustomSender:
        domain = email.split("@")[-1] if "@" in email else None
        row = await self._fetch_one(
            f"""
            INSERT INTO public.consultant_senders (
                consultant_id, email, domain, status, verification_token,
                created_at, updated_at
            ) VALUES ($1, $2, $3, 'pending', $4, NOW(), NOW())
            RETURNING {_SENDER_COLUMNS}
            """,
            consultant_id,
            email,
            domain,
            generate_verification_token(),
        )
        if row is None:
            raise RuntimeError("consultant_senders insert returned no row")
        return _row_to_sender(row)

    async def verify_sender(
        self, sender_id: str, consultant_id: str
    ) -> bool:
        """Mark a sender VERIFIED (Resend domain verification completes the
        underlying DNS proof; this records the outcome). Only VERIFIED senders
        may be used as a From address (D19 §13)."""
        row = await self._fetch_one(
            "UPDATE public.consultant_senders SET status = 'verified', "
            "verified_at = NOW(), updated_at = NOW() WHERE id = $1 "
            "AND consultant_id = $2 AND status = 'pending' RETURNING id",
            sender_id,
            consultant_id,
        )
        return row is not None

    async def remove_sender(self, sender_id: str, consultant_id: str) -> bool:
        row = await self._fetch_one(
            "UPDATE public.consultant_senders SET status = 'removed', "
            "removed_at = NOW(), updated_at = NOW() WHERE id = $1 "
            "AND consultant_id = $2 RETURNING id",
            sender_id,
            consultant_id,
        )
        return row is not None

    async def save(self, entity: CustomDomain) -> CustomDomain:
        return entity

    async def delete(self, id: str) -> None:  # noqa: A002 — abstract contract
        return None
