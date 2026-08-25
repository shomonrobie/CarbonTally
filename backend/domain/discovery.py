"""Existing-data discovery & direct-customer adoption domain (D27 / D19).

The customer-initiated direct-onboarding workflow. A customer who completes
normal signup may discover that CarbonTally already holds organizational data
that potentially matches theirs. This module is the pure domain model for that
workflow:

    lookup (candidate signals)          -> candidate organisations (CANDIDATE
                                           only — never authoritative)
    request                             -> pending_verification
    verify (email code / staff-mediated)-> verified
    choice (use_all | partial | discard)-> adopted | discarded

Security principle (D19 §6): organisation name, email domain, supplier name,
invoice data, consultant relationship and arbitrary user input are CANDIDATE
SIGNALS only. Adoption requires authenticated/authorized verification (control
of the candidate org's registered contact email, or CarbonTally-staff
mediation) and explicit customer choice. This module never authorizes by
itself — the API layer enforces membership + verification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

#: Discovery request lifecycle.
DISCOVERY_STATUSES: tuple[str, ...] = (
    "pending_verification",
    "verified",
    "adopted",
    "discarded",
    "expired",
    "rejected",
)

#: Adoption choices (D19 §7).
ADOPTION_CHOICES: tuple[str, ...] = ("use_all", "partial", "discard")

#: Adoption scope categories usable for a PARTIAL selection (D19 §8). The
#: selection is recorded for provenance; per-record partial-copy semantics are
#: NOT performed because the org-scoped schema would require unsafe duplication.
ADOPTION_SCOPE_CATEGORIES: tuple[str, ...] = (
    "documents",
    "suppliers",
    "extraction_records",
    "mappings",
    "calculations",
    "reports",
    "report_versions",
    "processing_history",
)

#: Verification methods.
VERIFICATION_METHODS: tuple[str, ...] = ("email", "staff_mediated")

#: Maximum verification attempts before a request is rejected (brute-force guard).
MAX_VERIFICATION_ATTEMPTS: int = 5

#: Verification code lifetime (seconds).
VERIFICATION_CODE_TTL_SECONDS: int = 15 * 60


@dataclass(frozen=True, slots=True)
class DiscoveryCandidate:
    """A potentially matching organisation (safe metadata only — never data)."""

    organization_id: str
    name: str
    country: Optional[str] = None
    industry: Optional[str] = None
    company_number: Optional[str] = None
    match_signal: str = "name"
    data_summary: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DiscoveryRequest:
    """A discovery/adoption request (``data_discovery_requests``).

    ``organization_id`` is the requesting (new) organisation. D35 makes it
    optional: ``None`` marks a PRE-ORG-CREATION self-service onboarding
    request initiated by an authenticated customer who does not yet belong to
    any organisation. ``created_by`` records that actor and is the only user
    allowed to verify / choose an outcome for an onboarding request.
    """

    id: str
    candidate_organization_id: str
    organization_id: Optional[str] = None
    created_by: Optional[str] = None
    status: str = "pending_verification"
    verification_method: str = "email"
    verification_code_hash: Optional[str] = None
    verification_code_expires_at: Optional[datetime] = None
    verification_attempts: int = 0
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    adoption_choice: Optional[str] = None
    adoption_scope: dict = field(default_factory=dict)
    adopted_at: Optional[datetime] = None
    adopted_by: Optional[str] = None
    discarded_at: Optional[datetime] = None
    discarded_by: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def validate_adoption_scope(choice: str, scope: Optional[dict]) -> tuple[bool, str]:
    """Validate a PARTIAL adoption selection.

    Returns ``(ok, message)``. For ``use_all``/``discard`` the scope must be
    empty/None; for ``partial`` every selected category must be in
    :data:`ADOPTION_SCOPE_CATEGORIES`.
    """
    if choice in ("use_all", "discard"):
        if scope:
            return False, f"adoption_scope must be empty for choice '{choice}'"
        return True, ""
    if choice == "partial":
        if not scope or not scope.get("categories"):
            return False, "partial adoption requires adoption_scope.categories"
        unknown = set(scope.get("categories", [])) - set(ADOPTION_SCOPE_CATEGORIES)
        if unknown:
            return False, f"unknown adoption categories: {sorted(unknown)}"
        return True, ""
    return False, f"unknown adoption choice '{choice}'"
