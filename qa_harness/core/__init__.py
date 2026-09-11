"""Core primitives shared by every QA Harness module.

These modules have NO dependency on the CarbonTally application and no
dependency on optional tools (Playwright, axe, Schemathesis, ...). They are
the deterministic, always-available foundation: finding model, secret
redaction, evidence path management, read-only safety, run status and
resolved configuration.
"""

from qa_harness.core.findings import (
    CATEGORIES,
    SEVERITIES,
    Deduplicator,
    Finding,
    FindingNormalizer,
    FindingStatus,
    normalize_text,
)
from qa_harness.core.safety import (
    BLOCKED_SAFE_MUTATION_NOT_AVAILABLE,
    MutationNotAvailable,
    ReadOnlyGuard,
)
from qa_harness.core.secrets import Redactor, default_redactor
from qa_harness.core.status import RunStatus, ToolUnavailable

__all__ = [
    "CATEGORIES",
    "SEVERITIES",
    "BLOCKED_SAFE_MUTATION_NOT_AVAILABLE",
    "Deduplicator",
    "Finding",
    "FindingNormalizer",
    "FindingStatus",
    "MutationNotAvailable",
    "ReadOnlyGuard",
    "Redactor",
    "RunStatus",
    "ToolUnavailable",
    "default_redactor",
    "normalize_text",
]
