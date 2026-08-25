"""Domain tests for the D27/D19 discovery workflow (validation + vocabulary)."""
from __future__ import annotations

from domain.discovery import (
    ADOPTION_SCOPE_CATEGORIES,
    validate_adoption_scope,
)
from domain.partners import (
    CLIENT_LIFECYCLE_STATUSES,
    can_transition_client_lifecycle,
)
from domain.whitelabel import DOMAIN_STATUSES, SENDER_STATUSES


class TestAdoptionScope:
    def test_use_all_requires_empty_scope(self) -> None:
        ok, _ = validate_adoption_scope("use_all", {})
        assert ok
        ok, _ = validate_adoption_scope("use_all", {"categories": ["documents"]})
        assert not ok

    def test_partial_requires_known_categories(self) -> None:
        ok, _ = validate_adoption_scope("partial", {"categories": ["documents"]})
        assert ok
        ok, _ = validate_adoption_scope("partial", {})
        assert not ok
        ok, _ = validate_adoption_scope("partial", {"categories": ["documents", "nope"]})
        assert not ok

    def test_discard_requires_empty_scope(self) -> None:
        ok, _ = validate_adoption_scope("discard", {})
        assert ok
        ok, _ = validate_adoption_scope("discard", {"categories": ["reports"]})
        assert not ok

    def test_unknown_choice_rejected(self) -> None:
        ok, _ = validate_adoption_scope("take_everything", {})
        assert not ok

    def test_categories_nonempty(self) -> None:
        assert ADOPTION_SCOPE_CATEGORIES


class TestLifecycleVocabulary:
    def test_statuses(self) -> None:
        assert "active" in CLIENT_LIFECYCLE_STATUSES
        assert "suspended" in CLIENT_LIFECYCLE_STATUSES
        assert "ended" in CLIENT_LIFECYCLE_STATUSES

    def test_ended_cannot_suspend(self) -> None:
        assert not can_transition_client_lifecycle("ended", "suspended")

    def test_new_grant_required_after_ended(self) -> None:
        assert can_transition_client_lifecycle("ended", "active")


class TestWhiteLabelVocabulary:
    def test_domain_statuses(self) -> None:
        assert DOMAIN_STATUSES == ("pending", "verified", "active", "removed_suspended")

    def test_sender_statuses(self) -> None:
        assert SENDER_STATUSES == ("pending", "verified", "removed")
