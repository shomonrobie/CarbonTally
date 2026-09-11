"""Normalized finding model for the CarbonTally QA Harness.

Every test method and every AI agent produces :class:`Finding` objects. The
finding model is deterministic and tool-independent:

* ID allocation is per-category (``QA-DB-001``, ``QA-RLS-002``, ...).
* Text normalization collapses near-identical phrasing ("No pagination in
  document table" vs "Documents table lacks pagination") into one canonical
  key used by the deduplicator.
* Deduplication preserves all evidence from every contributing source.

Severity vocabulary: P0 / P1 / P2 / P3 (see config/severity.yaml for the
business definitions).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Set

CATEGORIES = {
    "DB": "Database",
    "RLS": "Row-Level Security",
    "API": "API",
    "AUTH": "Authentication",
    "WF": "Workflow",
    "UI": "UI",
    "UX": "UX",
    "SEC": "Security",
    "A11Y": "Accessibility",
}

SEVERITIES = ("P0", "P1", "P2", "P3")

# Classification vocabulary (V1.2 calibration). A finding's classification
# decides whether it counts toward the acceptance verdict:
#
# * REAL                  — verified app defect (deterministic evidence).
# * RE-VERIFY             — candidate app finding that needs one confirming
#                           run before it is reported as current (e.g.
#                           org-bound 403s from the calibration sweep).
# * HARNESS_CONTRACT_DEFECT — the harness itself sent a request that violates
#                           the API contract (missing required params, wrong
#                           resource binding). NOT an app defect; reported in
#                           a separate "harness calibration" section.
# * INCONCLUSIVE          — the probe could not exercise the intended
#                           behavior (e.g. 422-on-empty-body for deny-gated
#                           mutations, fake-resource 404). Not counted.
# * SKIPPED / BLOCKED     — not run (tool unavailable / read-only boundary).
# * PO_DECISION_REQUIRED  — requirement ambiguous; needs a product decision.
class FindingClassification:
    # Application defects that count toward the verdict.
    REAL = "REAL"
    APPLICATION_DEFECT = "APPLICATION_DEFECT"
    REVERIFY = "RE-VERIFY"
    # Harness/tooling problems — never application defects.
    HARNESS_CONTRACT_DEFECT = "HARNESS_CONTRACT_DEFECT"
    HARNESS_RUNTIME_ERROR = "HARNESS_RUNTIME_ERROR"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    INCONCLUSIVE = "INCONCLUSIVE"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    PO_DECISION_REQUIRED = "PO_DECISION_REQUIRED"

    ALL = {
        REAL,
        APPLICATION_DEFECT,
        REVERIFY,
        HARNESS_CONTRACT_DEFECT,
        HARNESS_RUNTIME_ERROR,
        AUTHENTICATION_FAILURE,
        INCONCLUSIVE,
        SKIPPED,
        BLOCKED,
        PO_DECISION_REQUIRED,
    }

    # Classifications that count toward the acceptance verdict.
    VERDICT_COUNTED = {REAL, APPLICATION_DEFECT, REVERIFY}

# Status vocabulary used by findings and the Cline backlog generator.
class FindingStatus:
    OPEN = "OPEN"
    FIXED = "FIXED"
    VERIFIED = "VERIFIED"
    RECONFIRMED = "RECONFIRMED"
    NOT_IMPLEMENTED = "NOT IMPLEMENTED"
    NOT_TESTABLE = "NOT TESTABLE"
    ENVIRONMENT_BLOCKED = "ENVIRONMENT BLOCKED"
    PO_DECISION_REQUIRED = "PO DECISION REQUIRED"
    BLOCKED = "BLOCKED"
    WONTFIX = "WONTFIX"

    ALL = {
        OPEN,
        FIXED,
        VERIFIED,
        RECONFIRMED,
        NOT_IMPLEMENTED,
        NOT_TESTABLE,
        ENVIRONMENT_BLOCKED,
        PO_DECISION_REQUIRED,
        BLOCKED,
        WONTFIX,
    }


# --- Text normalization -----------------------------------------------------

# Synonym expansion applied BEFORE tokenization so that paraphrases converge
# onto a single canonical key. Keys are lowercase; values are the canonical
# token set (whitespace-split later).
_SYNONYMS: Dict[str, Set[str]] = {
    "pagination": {"pagination", "page", "paging", "pagecontrols"},
    "paging": {"pagination"},
    "table": {"table", "grid", "datagrid", "list"},
    "grid": {"table"},
    "document": {"document", "documents", "file", "files"},
    "no": {"no", "none", "not", "lacks", "lack", "missing", "absent", "zero"},
    "missing": {"no", "none", "not", "lacks", "lack", "missing", "absent", "zero"},
    "cannot": {"cannot", "cant", "unable", "unableto", "impossible"},
    "emissions": {"emission", "emissions", "co2e", "co2", "tco2e"},
    "organization": {"organization", "organisation", "org", "company", "customer"},
    "client": {"client", "customer"},
    "viewer": {"viewer", "readonly", "readonlyrole"},
    "admin": {"admin", "administrator"},
    "systemadmin": {"systemadmin", "systemadministrator"},
    "staffadmin": {"staffadmin", "staffadministrator"},
}


# Reverse lookup: every synonym value (plus its singular form) maps to the
# full canonical token set, so "documents"/"document" and "lacks"/"lack"
# converge onto the same expansion.
_SYNONYM_LOOKUP: Dict[str, Set[str]] = {}
for _words in _SYNONYMS.values():
    for _word in _words:
        targets = set(_words)
        if _word.endswith("s"):
            targets.add(_word[:-1])
        _SYNONYM_LOOKUP.setdefault(_word, set()).update(targets)
        if _word.endswith("s"):
            _SYNONYM_LOOKUP.setdefault(_word[:-1], set()).update(targets)


def _expand(word: str) -> Set[str]:
    """Expand one token into its canonical synonym set (identity if unknown)."""
    return _SYNONYM_LOOKUP.get(word, {word})


def normalize_text(text: str) -> str:
    """Return a canonical, order-insensitive key for a phrase.

    Steps: lowercase → strip non-alphanumerics → drop stopwords → expand
    synonyms → sort unique tokens → join. Two paraphrases that describe the
    same defect produce the same key.
    """
    if not text:
        return ""
    lowered = text.lower()
    tokens = re.findall(r"[a-z0-9]+", lowered)
    stopwords = {
        "the", "a", "an", "in", "on", "of", "to", "for", "and", "or", "but",
        "with", "is", "are", "was", "were", "be", "been", "has", "have",
        "had", "it", "its", "at", "by", "from", "as", "that", "this", "these",
        "those", "does", "do", "did", "will", "would", "should", "can",
    }
    expanded: Set[str] = set()
    for token in tokens:
        if token in stopwords:
            continue
        expanded |= _expand(token)
    return " ".join(sorted(expanded))


class FindingNormalizer:
    """Normalizes free-text fields of a finding into a canonical form."""

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    def key_for(self, title: str) -> str:
        """Canonical dedup key derived from a finding title."""
        if title in self._cache:
            return self._cache[title]
        key = normalize_text(title)
        self._cache[title] = key
        return key

    def normalize(self, finding: "Finding") -> "Finding":
        """Return the same finding with a canonical dedup key attached."""
        finding.normalized_key = self.key_for(finding.title)
        return finding


# --- Finding model ----------------------------------------------------------

@dataclass
class Finding:
    """A single normalized finding. Fields mirror the spec §28 model."""

    category: str                      # one of CATEGORIES keys
    severity: str                      # P0..P3
    title: str
    expected: str = ""
    actual: str = ""
    description: str = ""
    id: Optional[str] = None           # QA-<CAT>-<NNN>; allocated when None
    role: Optional[str] = None
    route: Optional[str] = None
    workflow: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    reproduction: List[str] = field(default_factory=list)
    business_impact: str = ""
    security_impact: str = ""
    root_cause: str = ""
    suggested_fix: str = ""
    status: str = FindingStatus.OPEN
    related_cline_task: str = ""
    classification: str = FindingClassification.REAL
    source: str = ""                   # e.g. "run_db.py", "ai:security_agent"
    timestamp: str = ""
    git_sha: str = ""
    dedup_group_size: int = 1          # number of merged duplicates
    # internal
    normalized_key: str = ""

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(
                f"Unknown category {self.category!r}; expected one of {sorted(CATEGORIES)}"
            )
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"Unknown severity {self.severity!r}; expected one of {SEVERITIES}"
            )
        if self.classification not in FindingClassification.ALL:
            raise ValueError(
                f"Unknown classification {self.classification!r}; expected one of "
                f"{sorted(FindingClassification.ALL)}"
            )
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not self.normalized_key:
            self.normalized_key = normalize_text(self.title)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "role": self.role,
            "route": self.route,
            "workflow": self.workflow,
            "expected": self.expected,
            "actual": self.actual,
            "description": self.description,
            "evidence": list(self.evidence),
            "reproduction": list(self.reproduction),
            "business_impact": self.business_impact,
            "security_impact": self.security_impact,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "status": self.status,
            "related_cline_task": self.related_cline_task,
            "classification": self.classification,
            "source": self.source,
            "timestamp": self.timestamp,
            "git_sha": self.git_sha,
            "normalized_key": self.normalized_key,
            "dedup_group_size": self.dedup_group_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Finding":
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in allowed}
        return cls(**kwargs)  # type: ignore[arg-type]


class FindingIdAllocator:
    """Per-category sequential ID allocation (QA-DB-001, QA-DB-002, ...)."""

    def __init__(self, start: int = 1) -> None:
        self._next: Dict[str, int] = {cat: start for cat in CATEGORIES}

    def allocate(self, category: str) -> str:
        n = self._next[category]
        self._next[category] = n + 1
        return f"QA-{category}-{n:03d}"


class Deduplicator:
    """Deterministic normalization + deduplication of findings.

    Grouping key = (category, normalized title key). The first finding seen in
    a group is the canonical representative; evidence lists from duplicates
    are merged and ``dedup_group_size`` records how many raw findings were
    folded into it.
    """

    def __init__(self, normalizer: Optional[FindingNormalizer] = None) -> None:
        self._normalizer = normalizer or FindingNormalizer()
        self._groups: Dict[tuple, List[Finding]] = {}
        self._order: List[tuple] = []

    def add(self, finding: Finding) -> Finding:
        """Add a finding; return the canonical group representative."""
        if finding.id is None:
            # Allocate a temporary id so every raw finding is identifiable.
            finding.id = f"RAW-{abs(hash(finding.normalized_key)):012d}"
        self._normalizer.normalize(finding)
        key = (finding.category, finding.normalized_key)
        if key not in self._groups:
            self._groups[key] = [finding]
            self._order.append(key)
            return finding
        group = self._groups[key]
        canonical = group[0]
        # Merge evidence from the duplicate (deduplicate identical strings).
        merged = list(canonical.evidence)
        for item in finding.evidence:
            if item not in merged:
                merged.append(item)
        canonical.evidence = merged
        canonical.dedup_group_size += 1
        group.append(finding)
        return canonical

    def deduplicated(self) -> List[Finding]:
        """Return canonical findings in first-seen order."""
        return [self._groups[k][0] for k in self._order]

    def raw_count(self) -> int:
        return sum(len(g) for g in self._groups.values())

    def group_sizes(self) -> Dict[str, int]:
        return {k[0] + ":" + k[1]: len(g) for k, g in self._groups.items()}


def renumber(findings: Sequence[Finding], allocator: Optional[FindingIdAllocator] = None) -> List[Finding]:
    """Assign stable QA-<CAT>-NNN ids in order; returns a new list.

    Deterministic (sorted by category then original id/title) so reports are
    reproducible across runs.
    """
    allocator = allocator or FindingIdAllocator()
    ordered = sorted(
        findings,
        key=lambda f: (f.category, f.id or "", f.title.lower()),
    )
    for finding in ordered:
        finding.id = allocator.allocate(finding.category)
    return list(ordered)


def normalize_finding(finding: Finding,
                      normalizer: Optional[FindingNormalizer] = None) -> Finding:
    """Return the finding with its canonical dedup key attached (spec §30)."""
    return (normalizer or FindingNormalizer()).normalize(finding)


def deduplicate_findings(findings: Iterable[Finding]) -> List[Finding]:
    """Normalize + deduplicate + assign stable QA ids in one pass (spec §30)."""
    dedup = Deduplicator()
    for finding in findings:
        dedup.add(finding)
    return renumber(dedup.deduplicated())


def filter_by(findings: Iterable[Finding], **criteria: Optional[str]) -> List[Finding]:
    """Filter findings by field values (None criteria are ignored)."""
    result = []
    for f in findings:
        match = True
        for field_name, value in criteria.items():
            if value is None:
                continue
            if getattr(f, field_name, None) != value:
                match = False
                break
        if match:
            result.append(f)
    return result
