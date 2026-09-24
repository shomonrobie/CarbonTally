"""P12-IMPL-02 — organisation-scoped supplier resolution (Decision-01 §17–§19).

Implements the approved supplier-resolution contract:

    EXTRACT -> NORMALIZE -> FIND ORG-SCOPED CANDIDATES -> SCORE/CLASSIFY
            -> CONFIRM WHEN REQUIRED -> CREATE WHEN REQUIRED -> PERSIST -> REUSE

Design rules (all deliberate, all fail-closed):

* **Pure and deterministic** — no I/O, no database, no AI, no randomness. Candidate
  discovery is performed by the caller through the existing, already organisation-scoped
  repository (``repos.suppliers.search_for_org``); this module only normalises, scores and
  classifies.
* **Organisation-scoped** — every candidate must carry the same ``organization_id`` as the
  resolution request; a candidate from another organisation is rejected outright
  (``cross_tenant_candidate``), so org-A can never resolve to org-B's supplier.
* **Never silently choose** — two candidates within the margin produce ``ambiguous`` and
  require operator selection (P12-D4).
* **Never silently create** — ``none`` produces ``confirm_creation`` which requires
  operator confirmation through the existing authorised creation workflow (P12-D3).
* **Never fabricate** — a missing/blank extracted supplier yields ``unresolved``
  (manual review), never a guess.

Only an ``exact`` verdict may be persisted automatically (P12-D2).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# ── verdicts ────────────────────────────────────────────────────────────────
VERDICT_EXACT = "exact"
VERDICT_STRONG = "strong"
VERDICT_PROBABLE = "probable"
VERDICT_AMBIGUOUS = "ambiguous"
VERDICT_NONE = "none"
VERDICT_UNRESOLVED = "unresolved"

#: The only verdict that may be persisted without operator confirmation.
AUTO_PERSIST_VERDICTS = (VERDICT_EXACT,)

#: Actions the caller should take (never "guess", never "create silently").
ACTION_REUSE = "reuse"
ACTION_CONFIRM_MATCH = "confirm_match"
ACTION_SELECT_CANDIDATE = "select_candidate"
ACTION_CONFIRM_CREATION = "confirm_creation"
ACTION_MANUAL_REVIEW = "manual_review"

#: Legal-form tokens collapsed **for comparison only**; the stored name is never rewritten.
_LEGAL_FORMS = {
    "ltd", "limited", "plc", "llp", "lp", "inc", "incorporated", "corp",
    "corporation", "co", "company", "gmbh", "sa", "bv",
}
_PUNCT = re.compile(r"[^\w\s]+")
_WS = re.compile(r"\s+")
#: UK postcode, normalised by removing spaces (e.g. ``QI14 5ZD`` -> ``QI145ZD``).
_POSTCODE = re.compile(r"^[A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2}$")


def normalise_name(value: Optional[str]) -> str:
    """Comparison form of a company name (never the stored form)."""
    if not value:
        return ""
    text = str(value).strip().casefold().replace("&", " and ")
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    tokens = [t for t in text.split(" ") if t and t not in _LEGAL_FORMS]
    return " ".join(tokens)


def name_tokens(value: Optional[str]) -> frozenset[str]:
    return frozenset(normalise_name(value).split(" "))


def normalise_postcode(value: Optional[str]) -> str:
    if not value:
        return ""
    compact = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return compact if _POSTCODE.match(compact) else compact


def normalise_identifier(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^0-9A-Za-z]", "", str(value)).upper()


@dataclass(frozen=True)
class ResolutionSignals:
    """Signals available from the extracted document (all optional)."""

    supplier_name: str = ""
    postcode: str = ""
    vat_number: str = ""
    company_number: str = ""
    address_line1: str = ""
    city: str = ""
    email_domain: str = ""

    @property
    def usable(self) -> bool:
        return bool(self.supplier_name.strip())


def signals_from_extracted(extracted_data: dict[str, Any] | None) -> ResolutionSignals:
    """Build signals from an extraction payload (missing keys stay empty)."""
    data = extracted_data or {}
    return ResolutionSignals(
        supplier_name=str(data.get("supplier") or ""),
        postcode=str(data.get("supplier_postcode") or ""),
        vat_number=str(data.get("supplier_vat_number") or ""),
        company_number=str(data.get("supplier_company_number") or ""),
        address_line1=str(data.get("supplier_address_line1") or ""),
        city=str(data.get("supplier_city") or ""),
        email_domain=str(data.get("supplier_email_domain") or ""),
    )


@dataclass
class Candidate:
    """One org-scoped candidate supplier under consideration."""

    supplier_id: str
    organization_id: str
    name: str
    postcode: str = ""
    vat_number: str = ""
    company_number: str = ""
    address_line1: str = ""
    city: str = ""
    email_domain: str = ""


@dataclass
class ScoredCandidate:
    candidate: Candidate
    score: int
    signals: list[str] = field(default_factory=list)


@dataclass
class ResolutionOutcome:
    """The resolution decision, with everything an auditor needs."""

    verdict: str
    action: str
    reason: str
    signals: ResolutionSignals
    scored: list[ScoredCandidate] = field(default_factory=list)
    selected: Optional[Candidate] = None
    rejected: list[dict[str, str]] = field(default_factory=list)
    auto_persist: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "action": self.action,
            "reason": self.reason,
            "auto_persist": self.auto_persist,
            "signals": {
                "supplier_name": self.signals.supplier_name,
                "postcode": self.signals.postcode,
            },
            "candidates": [
                {"supplier_id": s.candidate.supplier_id, "name": s.candidate.name,
                 "score": s.score, "signals": s.signals}
                for s in self.scored
            ],
            "selected_supplier_id": self.selected.supplier_id if self.selected else None,
            "rejected": self.rejected,
        }


def score_candidate(signals: ResolutionSignals, candidate: Candidate) -> ScoredCandidate:
    """Deterministic weighted scoring using only signals the document carries."""
    score = 0
    matched: list[str] = []

    req_vat = normalise_identifier(signals.vat_number)
    cand_vat = normalise_identifier(candidate.vat_number)
    if req_vat and cand_vat and req_vat == cand_vat:
        score += 100
        matched.append("vat_number")

    req_co = normalise_identifier(signals.company_number)
    cand_co = normalise_identifier(candidate.company_number)
    if req_co and cand_co and req_co == cand_co:
        score += 100
        matched.append("company_number")

    req_pc = normalise_postcode(signals.postcode)
    cand_pc = normalise_postcode(candidate.postcode)
    if req_pc and cand_pc and req_pc == cand_pc:
        score += 30
        matched.append("postcode")

    req_name = normalise_name(signals.supplier_name)
    cand_name = normalise_name(candidate.name)
    if req_name and cand_name:
        if req_name == cand_name:
            score += 40
            matched.append("name_exact")
        else:
            a, b = name_tokens(signals.supplier_name), name_tokens(candidate.name)
            shared = a & b
            if shared:
                jaccard = len(shared) / len(a | b)
                if jaccard >= 0.5:
                    score += 20
                    matched.append(f"name_similarity:{jaccard:.2f}")

    req_addr = normalise_name(signals.address_line1)
    cand_addr = normalise_name(candidate.address_line1)
    if req_addr and cand_addr and req_addr == cand_addr:
        score += 15
        matched.append("address_line1")

    req_city = normalise_name(signals.city)
    cand_city = normalise_name(candidate.city)
    if req_city and cand_city and req_city == cand_city:
        score += 10
        matched.append("city")

    req_dom = str(signals.email_domain or "").strip().casefold()
    cand_dom = str(candidate.email_domain or "").strip().casefold()
    if req_dom and cand_dom and req_dom == cand_dom:
        score += 5
        matched.append("email_domain")

    return ScoredCandidate(candidate=candidate, score=score, signals=matched)


#: Score margin below which two candidates are considered indistinguishable.
AMBIGUITY_MARGIN = 10


def classify(
    signals: ResolutionSignals,
    candidates: Iterable[Candidate],
    organization_id: str,
) -> ResolutionOutcome:
    """Classify org-scoped candidates into a verdict + the action the caller must take."""
    if not signals.usable:
        return ResolutionOutcome(
            verdict=VERDICT_UNRESOLVED, action=ACTION_MANUAL_REVIEW,
            reason="no supplier text was extracted from the document", signals=signals,
        )

    rejected = [
        {"supplier_id": c.supplier_id, "reason": "cross_tenant_candidate"}
        for c in candidates if c.organization_id != organization_id
    ]
    scored = sorted(
        (score_candidate(signals, c) for c in candidates
         if c.organization_id == organization_id),
        key=lambda s: (-s.score, s.candidate.supplier_id),
    )
    scored = [s for s in scored if s.score > 0]

    if not scored:
        return ResolutionOutcome(
            verdict=VERDICT_NONE, action=ACTION_CONFIRM_CREATION,
            reason="no existing supplier in this organisation matches the extracted name",
            signals=signals, rejected=rejected,
        )

    best = scored[0]
    runner_up = scored[1] if len(scored) > 1 else None

    if runner_up and (best.score - runner_up.score) < AMBIGUITY_MARGIN:
        return ResolutionOutcome(
            verdict=VERDICT_AMBIGUOUS, action=ACTION_SELECT_CANDIDATE,
            reason=(f"two or more plausible suppliers for {signals.supplier_name!r} "
                    f"(margin {best.score - runner_up.score} < {AMBIGUITY_MARGIN})"),
            signals=signals, scored=scored, rejected=rejected,
        )

    has_identifier = bool(
        normalise_identifier(signals.vat_number)
        or normalise_identifier(signals.company_number)
    )
    name_exact = "name_exact" in best.signals
    corroborated = bool({"postcode", "address_line1", "city"} & set(best.signals))

    if (
        (has_identifier and "vat_number" in best.signals)
        or "company_number" in best.signals
        or (name_exact and corroborated)
    ):
        return ResolutionOutcome(
            verdict=VERDICT_EXACT, action=ACTION_REUSE,
            reason=f"exact organisation-scoped match on {', '.join(best.signals)}",
            signals=signals, scored=scored, selected=best.candidate,
            rejected=rejected, auto_persist=True,
        )

    if name_exact:
        return ResolutionOutcome(
            verdict=VERDICT_STRONG, action=ACTION_CONFIRM_MATCH,
            reason="supplier name matches exactly but no address/identifier corroborates it",
            signals=signals, scored=scored, selected=best.candidate, rejected=rejected,
        )

    return ResolutionOutcome(
        verdict=VERDICT_PROBABLE, action=ACTION_CONFIRM_MATCH,
        reason=f"similar supplier name ({', '.join(best.signals)}) requires confirmation",
        signals=signals, scored=scored, selected=best.candidate, rejected=rejected,
    )
