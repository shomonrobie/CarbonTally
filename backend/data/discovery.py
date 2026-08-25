"""Existing-data discovery repository (D27 / D19).

Persistence for ``data_discovery_requests`` (the customer-initiated
existing-data adoption workflow) plus the discovery lookup surface. The
repository is service-role only; the API re-authorizes every request
(org membership of the requesting org + verification state) before any write.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.discovery import (
    DiscoveryCandidate,
    DiscoveryRequest,
    MAX_VERIFICATION_ATTEMPTS,
    VERIFICATION_CODE_TTL_SECONDS,
)

_DISCOVERY_COLUMNS = (
    "id, organization_id, candidate_organization_id, status, verification_method, "
    "verification_code_hash, verification_code_expires_at, verification_attempts, "
    "verified_at, verified_by, adoption_choice, adoption_scope, adopted_at, "
    "adopted_by, discarded_at, discarded_by, note, created_at, updated_at, created_by"
)


def hash_verification_code(code: str) -> str:
    """SHA-256 of the verification code (never store the plaintext code)."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_verification_code() -> str:
    """Cryptographically random 8-character verification code (URL-safe)."""
    return secrets.token_urlsafe(8)


def _row_to_discovery_request(row: Any) -> DiscoveryRequest:
    r = dict(row)
    return DiscoveryRequest(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]) if r.get("organization_id") else None,
        candidate_organization_id=str(r["candidate_organization_id"]),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
        status=str(r["status"]),
        verification_method=str(r.get("verification_method") or "email"),
        verification_code_hash=r.get("verification_code_hash"),
        verification_code_expires_at=r.get("verification_code_expires_at"),
        verification_attempts=int(r.get("verification_attempts") or 0),
        verified_at=r.get("verified_at"),
        verified_by=str(r["verified_by"]) if r.get("verified_by") else None,
        adoption_choice=r.get("adoption_choice"),
        adoption_scope=loads_jsonb(r.get("adoption_scope")) or {},
        adopted_at=r.get("adopted_at"),
        adopted_by=str(r["adopted_by"]) if r.get("adopted_by") else None,
        discarded_at=r.get("discarded_at"),
        discarded_by=str(r["discarded_by"]) if r.get("discarded_by") else None,
        note=r.get("note"),
        created_at=r.get("created_at"),
        updated_at=r.get("updated_at"),
    )

class DiscoveryRepository(AbstractRepository[DiscoveryRequest]):
    """Service-role persistence for discovery/adoption requests."""

    # -- read ----------------------------------------------------------------
    async def get(self, request_id: str) -> Optional[DiscoveryRequest]:
        row = await self._fetch_one(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE id = $1",
            request_id,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def get_for_org(
        self, request_id: str, organization_id: str
    ) -> Optional[DiscoveryRequest]:
        """Return the request only when ``organization_id`` (the requesting
        org) owns it — the API-level ownership re-check."""
        row = await self._fetch_one(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE id = $1 AND organization_id = $2",
            request_id,
            organization_id,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def get_for_onboarding(
        self, request_id: str, created_by: str
    ) -> Optional[DiscoveryRequest]:
        """Return a PRE-ORG-CREATION (``organization_id IS NULL``) onboarding
        request only when ``created_by`` initiated it — the no-org analogue of
        ``get_for_org`` ownership scoping (D35)."""
        row = await self._fetch_one(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE id = $1 AND organization_id IS NULL AND created_by = $2",
            request_id,
            created_by,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def get_onboarding_by_candidate(
        self, candidate_organization_id: str, created_by: str
    ) -> Optional[DiscoveryRequest]:
        """Return the actor's existing live onboarding request for a candidate
        organisation, if any (drives the partial unique index + resume path)."""
        row = await self._fetch_one(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE candidate_organization_id = $1 AND organization_id IS NULL "
            "AND created_by = $2 AND status IN ('pending_verification', 'verified') "
            "ORDER BY created_at DESC LIMIT 1",
            candidate_organization_id,
            created_by,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def list_for_org(self, organization_id: str) -> list[DiscoveryRequest]:
        rows = await self._fetch_all(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE organization_id = $1 ORDER BY created_at DESC",
            organization_id,
        )
        return [_row_to_discovery_request(r) for r in rows]

    async def get_for_candidate(
        self, organization_id: str, candidate_organization_id: str
    ) -> Optional[DiscoveryRequest]:
        row = await self._fetch_one(
            f"SELECT {_DISCOVERY_COLUMNS} FROM public.data_discovery_requests "
            "WHERE organization_id = $1 AND candidate_organization_id = $2",
            organization_id,
            candidate_organization_id,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def count_for_candidate(self, candidate_organization_id: str) -> int:
        row = await self._fetch_one(
            "SELECT COUNT(*) FROM public.data_discovery_requests "
            "WHERE candidate_organization_id = $1 AND status IN "
            "('pending_verification', 'verified', 'adopted')",
            candidate_organization_id,
        )
        return int(row[0]) if row is not None else 0


    # -- discovery lookup (candidate signals only, never authoritative) ------
    async def lookup_candidates(
        self,
        *,
        name: Optional[str] = None,
        company_number: Optional[str] = None,
        email_domain: Optional[str] = None,
        contact_email: Optional[str] = None,
        limit: int = 10,
    ) -> list[DiscoveryCandidate]:
        """Find POTENTIALLY matching organisations from candidate signals.

        This is a discovery aid, NOT an ownership determination (D19 §6).
        Returns safe metadata + per-org data counts only — never customer
        data rows.
        """
        conditions: list[str] = []
        args: list[Any] = []
        if name:
            conditions.append("(o.name ILIKE '%%' || $%d || '%%')" % (len(args) + 1))
            args.append(name.strip())
        if company_number:
            conditions.append("o.company_number = $%d" % (len(args) + 1))
            args.append(company_number.strip())
        if email_domain:
            conditions.append(
                "LOWER(o.primary_contact_email) LIKE '%%@%s'"
                % email_domain.strip().lower().replace("%", "%%")
            )
        if contact_email:
            conditions.append(
                "LOWER(o.primary_contact_email) = $%d" % (len(args) + 1)
            )
            args.append(contact_email.strip().lower())
        if not conditions:
            return []
        where = " OR ".join(conditions)
        query = (
            "SELECT o.id, o.name, o.country, o.industry, o.company_number "
            "FROM public.organizations o "
            "WHERE o.is_active = TRUE AND (%s) "
            "ORDER BY o.created_at DESC LIMIT %d" % (where, int(limit))
        )
        rows = await self._fetch_all(query, *args)
        candidates: list[DiscoveryCandidate] = []
        for row in rows:
            org_id = str(row["id"])
            summary = await self._org_data_summary(org_id)
            candidates.append(
                DiscoveryCandidate(
                    organization_id=org_id,
                    name=str(row["name"]),
                    country=row.get("country"),
                    industry=row.get("industry"),
                    company_number=row.get("company_number"),
                    match_signal="candidate",
                    data_summary=summary,
                )
            )
        return candidates


    async def _org_data_summary(self, organization_id: str) -> dict[str, int]:
        """Safe per-org data COUNTS for the discovery review screen."""
        summary: dict[str, int] = {}
        tables = {
            "documents": "organization_files",
            "suppliers": "suppliers",
            "emissions_logs": "emissions_logs",
            "calculation_snapshots": "calculation_snapshots",
            "report_versions": "report_versions",
            "extraction_batches": "manual_extraction_batches",
        }
        for key, table in tables.items():
            try:
                row = await self._fetch_one(
                    f"SELECT COUNT(*) FROM public.{table} WHERE organization_id = $1",
                    organization_id,
                )
                summary[key] = int(row[0]) if row is not None else 0
            except Exception:  # noqa: BLE001 — best-effort counts
                summary[key] = 0
        return summary

    # -- verification --------------------------------------------------------
    async def create_request(
        self,
        *,
        organization_id: str,
        candidate_organization_id: str,
        verification_method: str = "email",
        note: Optional[str] = None,
    ) -> DiscoveryRequest:
        row = await self._fetch_one(
            "INSERT INTO public.data_discovery_requests ("
            "    organization_id, candidate_organization_id, status,"
            "    verification_method, note, created_at, updated_at"
            ") VALUES ($1, $2, 'pending_verification', $3, $4, NOW(), NOW())"
            f" RETURNING {_DISCOVERY_COLUMNS}",
            organization_id,
            candidate_organization_id,
            verification_method,
            note,
        )
        if row is None:
            raise RuntimeError("data_discovery_requests insert returned no row")
        return _row_to_discovery_request(row)

    async def create_onboarding_request(
        self,
        *,
        candidate_organization_id: str,
        created_by: str,
        verification_method: str = "email",
        note: Optional[str] = None,
    ) -> DiscoveryRequest:
        """Create a PRE-ORG-CREATION discovery request (``organization_id``
        NULL, D35). ``created_by`` binds the request to the authenticated
        customer who may verify / choose an outcome for it."""
        row = await self._fetch_one(
            "INSERT INTO public.data_discovery_requests ("
            "    organization_id, candidate_organization_id, status,"
            "    verification_method, note, created_by, created_at, updated_at"
            ") VALUES (NULL, $1, 'pending_verification', $2, $3, $4, NOW(), NOW())"
            f" RETURNING {_DISCOVERY_COLUMNS}",
            candidate_organization_id,
            verification_method,
            note,
            created_by,
        )
        if row is None:
            raise RuntimeError("data_discovery_requests insert returned no row")
        return _row_to_discovery_request(row)


    async def store_verification_code(
        self,
        request_id: str,
        code: str,
        *,
        ttl_seconds: int = VERIFICATION_CODE_TTL_SECONDS,
    ) -> Optional[DiscoveryRequest]:
        row = await self._fetch_one(
            "UPDATE public.data_discovery_requests "
            "SET verification_code_hash = $2,"
            "    verification_code_expires_at = NOW() + ($3 * interval '1 second'),"
            "    verification_attempts = 0, status = 'pending_verification',"
            "    updated_at = NOW()"
            " WHERE id = $1"
            f" RETURNING {_DISCOVERY_COLUMNS}",
            request_id,
            hash_verification_code(code),
            ttl_seconds,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def verify_code(
        self, request_id: str, code: str, *, verified_by: str
    ) -> tuple[bool, str]:
        """Verify a submitted code.

        Returns ``(ok, reason)``. Failures increment ``verification_attempts``;
        after ``MAX_VERIFICATION_ATTEMPTS`` the request is rejected.
        """
        request = await self.get(request_id)
        if request is None:
            return False, "request not found"
        if request.status != "pending_verification":
            return False, f"request is not pending verification (status={request.status})"
        if request.verification_attempts >= MAX_VERIFICATION_ATTEMPTS:
            await self._mark_rejected(request_id)
            return False, "too many verification attempts — request rejected"
        if not request.verification_code_hash or not request.verification_code_expires_at:
            return False, "no verification code issued"
        if request.verification_code_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return False, "verification code expired"
        if hash_verification_code(code.strip()) != request.verification_code_hash:
            await self._increment_attempts(request_id)
            return False, "invalid verification code"
        await self._mark_verified(request_id, verified_by)
        return True, "verified"


    async def _increment_attempts(self, request_id: str) -> None:
        row = await self._fetch_one(
            "SELECT verification_attempts FROM public.data_discovery_requests "
            "WHERE id = $1",
            request_id,
        )
        attempts = int(row[0]) if row is not None else 0
        await self._execute(
            "UPDATE public.data_discovery_requests SET verification_attempts = $2, "
            "updated_at = NOW() WHERE id = $1",
            request_id,
            attempts + 1,
        )
        if attempts + 1 >= MAX_VERIFICATION_ATTEMPTS:
            await self._mark_rejected(request_id)

    async def _mark_verified(self, request_id: str, verified_by: str) -> None:
        await self._execute(
            "UPDATE public.data_discovery_requests SET status = 'verified', "
            "verified_at = NOW(), verified_by = $2, updated_at = NOW() "
            "WHERE id = $1",
            request_id,
            verified_by,
        )

    async def _mark_rejected(self, request_id: str) -> None:
        await self._execute(
            "UPDATE public.data_discovery_requests SET status = 'rejected', "
            "updated_at = NOW() WHERE id = $1",
            request_id,
        )

    async def staff_verify(self, request_id: str, *, verified_by: str) -> bool:
        """CarbonTally-staff-mediated verification (operational fallback when
        email delivery is unavailable). The API layer enforces staff authority."""
        row = await self._fetch_one(
            "UPDATE public.data_discovery_requests SET status = 'verified', "
            "verified_at = NOW(), verified_by = $2, updated_at = NOW() "
            "WHERE id = $1 AND status = 'pending_verification'",
            request_id,
            verified_by,
        )
        return row is not None


    # -- adoption / discard --------------------------------------------------
    async def adopt(
        self,
        request_id: str,
        *,
        choice: str,
        scope: Optional[dict],
        adopted_by: str,
    ) -> Optional[DiscoveryRequest]:
        row = await self._fetch_one(
            "UPDATE public.data_discovery_requests "
            "SET status = 'adopted', adoption_choice = $2, adoption_scope = $3,"
            "    adopted_at = NOW(), adopted_by = $4, updated_at = NOW()"
            " WHERE id = $1"
            f" RETURNING {_DISCOVERY_COLUMNS}",
            request_id,
            choice,
            dumps_jsonb(scope or {}),
            adopted_by,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def discard(
        self, request_id: str, *, discarded_by: str, note: Optional[str] = None
    ) -> Optional[DiscoveryRequest]:
        """DISCARD records the decision ONLY — it never deletes any data (D19 §7)."""
        row = await self._fetch_one(
            "UPDATE public.data_discovery_requests "
            "SET status = 'discarded', adoption_choice = 'discard',"
            "    discarded_at = NOW(), discarded_by = $2, note = COALESCE($3, note),"
            "    updated_at = NOW()"
            " WHERE id = $1"
            f" RETURNING {_DISCOVERY_COLUMNS}",
            request_id,
            discarded_by,
            note,
        )
        return _row_to_discovery_request(row) if row is not None else None

    async def save(self, entity: DiscoveryRequest) -> DiscoveryRequest:
        return entity

    async def delete(self, id: str) -> None:  # noqa: A002 — abstract contract
        return None

