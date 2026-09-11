"""Read-only safety enforcement (spec §33).

The harness default mode is READ ONLY. Any future mutation test must:

* explicitly declare mutation (``ReadOnlyGuard.declare_mutation``),
* use isolated QA records tagged with a QA prefix,
* clean up only records created by that test,
* verify cleanup,
* never delete investor-demo data,
* never reset the database.

If safe mutation cannot be guaranteed the check reports
``BLOCKED — SAFE MUTATION NOT AVAILABLE`` instead of improvising.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set

BLOCKED_SAFE_MUTATION_NOT_AVAILABLE = "BLOCKED — SAFE MUTATION NOT AVAILABLE"

# Prefix used to tag records created by QA mutation tests so they can be
# found and removed without touching investor-demo data.
QA_TAG_PREFIX = "qa_harness_"


class GuardMode(str, Enum):
    READ_ONLY = "read-only"
    MUTATION = "mutation"


class MutationNotAvailable(RuntimeError):
    """Raised when a mutation cannot be performed safely."""

    def __init__(self, reason: str = "") -> None:
        super().__init__(BLOCKED_SAFE_MUTATION_NOT_AVAILABLE + (f": {reason}" if reason else ""))
        self.reason = reason


@dataclass
class MutationDeclaration:
    """A declared, self-contained mutation scope."""

    test_id: str
    description: str
    tag: str = QA_TAG_PREFIX
    created_record_ids: Set[str] = field(default_factory=set)
    cleanup_verified: bool = False


class ReadOnlyGuard:
    """Central gate for every write the harness might ever attempt.

    Default mode is ``READ_ONLY``; in that mode any write attempt raises
    :class:`MutationNotAvailable`. Mutation mode is only entered via an
    explicit :meth:`declare_mutation` and every mutation must be cleaned up.
    """

    def __init__(self, mode: GuardMode = GuardMode.READ_ONLY) -> None:
        self.mode = mode
        self._active_mutation: Optional[MutationDeclaration] = None
        self._declarations: List[MutationDeclaration] = []

    def require_read_only(self) -> None:
        """Ensure no write is in progress. Called by every DB/API write path
        before executing; raises if a mutation scope is not active."""
        if self.mode is GuardMode.READ_ONLY:
            raise MutationNotAvailable("harness is in read-only mode")
        if self._active_mutation is None:
            raise MutationNotAvailable("write attempted outside a declared mutation scope")

    def declare_mutation(self, test_id: str, description: str) -> MutationDeclaration:
        """Explicitly opt in to mutation for one self-contained test."""
        if self.mode is GuardMode.READ_ONLY:
            raise MutationNotAvailable("cannot declare mutation while guard is read-only")
        declaration = MutationDeclaration(test_id=test_id, description=description)
        self._declarations.append(declaration)
        self._active_mutation = declaration
        return declaration

    def record_created(self, record_id: str) -> None:
        """Record a record id created by the active mutation test."""
        if self._active_mutation is None:
            raise MutationNotAvailable("no active mutation scope")
        self._active_mutation.created_record_ids.add(record_id)

    @property
    def created_ids(self) -> Set[str]:
        if self._active_mutation is None:
            return set()
        return set(self._active_mutation.created_record_ids)

    def finish_mutation(self, cleanup_verified: bool) -> None:
        """End the active mutation scope; cleanup must be verified."""
        if self._active_mutation is None:
            return
        self._active_mutation.cleanup_verified = cleanup_verified
        self._active_mutation = None

    def is_safe(self) -> bool:
        """True when no mutation is active (i.e. everything is read-only)."""
        return self._active_mutation is None
