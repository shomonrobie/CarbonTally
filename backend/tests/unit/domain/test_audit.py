"""Unit tests for domain.audit."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.audit import AuditEntry, AuditTrail


def make_entry(
    entry_id: str = "a-1",
    correlation_id: str = "corr-1",
    action: str = "created",
    entity_id: str = "doc-1",
) -> AuditEntry:
    return AuditEntry(
        id=entry_id,
        correlation_id=correlation_id,
        entity_type="document",
        entity_id=entity_id,
        action=action,
        actor="system",
        occurred_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        changed_fields={"status": "uploaded"},
        reason="initial upload",
        ip_address=None,
        before=None,
        after={"status": "uploaded"},
    )


class TestAuditEntry:
    def test_constructs(self) -> None:
        entry = make_entry()
        assert entry.action == "created"
        assert entry.changed_fields == {"status": "uploaded"}
        assert entry.reason == "initial upload"

    def test_defaults(self) -> None:
        entry = make_entry()
        assert entry.ip_address is None
        assert entry.before is None

    def test_is_immutable(self) -> None:
        entry = make_entry()
        with pytest.raises(FrozenInstanceError):
            entry.action = "deleted"  # type: ignore[misc]


class TestAuditTrail:
    def test_constructs(self) -> None:
        trail = AuditTrail(
            correlation_id="corr-1",
            entries=(make_entry(), make_entry(entry_id="a-2", action="activated")),
        )
        assert len(trail.entries) == 2

    def test_rejects_mismatched_correlation(self) -> None:
        with pytest.raises(ValueError):
            AuditTrail(
                correlation_id="corr-1",
                entries=(make_entry(correlation_id="other"),),
            )

    def test_by_action(self) -> None:
        trail = AuditTrail(
            correlation_id="corr-1",
            entries=(
                make_entry(entry_id="a-1", action="created"),
                make_entry(entry_id="a-2", action="activated"),
                make_entry(entry_id="a-3", action="created"),
            ),
        )
        assert [e.id for e in trail.by_action("created")] == ["a-1", "a-3"]
        assert [e.id for e in trail.by_action("deleted")] == []

    def test_by_entity(self) -> None:
        trail = AuditTrail(
            correlation_id="corr-1",
            entries=(
                make_entry(entry_id="a-1", entity_id="doc-1"),
                make_entry(entry_id="a-2", entity_id="doc-2"),
                make_entry(entry_id="a-3", entity_id="doc-1"),
            ),
        )
        assert [e.id for e in trail.by_entity("document", "doc-1")] == ["a-1", "a-3"]
