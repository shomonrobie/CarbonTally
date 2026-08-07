"""Unit tests for infra.event_bus."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import pytest

from domain.workflow import DocumentUploaded, DomainEvent, ImportStarted
from infra.event_bus import EventBus, get_event_bus, reset_event_bus


def _document_event(**kwargs: Any) -> DocumentUploaded:
    return DocumentUploaded(
        event_id=str(kwargs.get("event_id") or "event-1"),
        occurred_at=datetime(2025, 6, 1, 12, 0, 0),
        correlation_id=str(kwargs.get("correlation_id") or "corr-1"),
        document_id=str(kwargs.get("document_id") or "doc-1"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        storage_path=str(kwargs.get("storage_path") or "uploads/invoice.pdf"),
    )


class TestSubscribe:
    async def test_sync_handler_receives_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(DocumentUploaded, handler)
        await bus.publish_and_wait(_document_event())
        assert len(received) == 1
        entry = received[0]
        assert isinstance(entry, DocumentUploaded)
        assert entry.document_id == "doc-1"
        assert entry.aggregate_type == "document"

    async def test_async_handler_receives_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(DocumentUploaded, handler)
        await bus.publish_and_wait(_document_event())
        assert len(received) == 1

    async def test_wildcard_handler_receives_every_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(None, handler)
        await bus.publish_and_wait(_document_event())
        await bus.publish_and_wait(
            ImportStarted(
                event_id="event-2",
                occurred_at=datetime(2025, 6, 1, 12, 0, 0),
                correlation_id="corr-2",
                batch_id="batch-1",
                provider_key="defra",
            )
        )
        assert [type(e).__name__ for e in received] == [
            "DocumentUploaded",
            "ImportStarted",
        ]

    async def test_only_matching_event_types_dispatch(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(ImportStarted, handler)
        await bus.publish_and_wait(_document_event())
        assert received == []

    def test_duplicate_subscription_raises(self) -> None:
        bus = EventBus()
        handler = lambda event: None  # noqa: E731
        bus.subscribe(DocumentUploaded, handler)
        with pytest.raises(ValueError, match="already subscribed"):
            bus.subscribe(DocumentUploaded, handler)

    def test_max_handlers_limit_enforced(self) -> None:
        bus = EventBus(max_handlers=2)
        bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731
        bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731
        with pytest.raises(ValueError, match="too many handlers"):
            bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731

    def test_max_handlers_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            EventBus(max_handlers=0)

    async def test_unsubscribe(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []
        handler = lambda event: received.append(event)  # noqa: E731
        bus.subscribe(DocumentUploaded, handler)
        assert bus.unsubscribe(DocumentUploaded, handler) is True
        assert bus.unsubscribe(DocumentUploaded, handler) is False
        await bus.publish_and_wait(_document_event())
        assert received == []

    async def test_clear_drops_all_handlers(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []
        bus.subscribe(None, lambda event: received.append(event))  # noqa: E731
        bus.clear()
        await bus.publish_and_wait(_document_event())
        assert received == []

    async def test_subscriber_count(self) -> None:
        bus = EventBus()
        bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731
        bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731
        bus.subscribe(None, lambda e: None)  # noqa: E731
        assert bus.subscriber_count(DocumentUploaded) == 2
        assert bus.subscriber_count(None) == 3


class TestPublish:
    async def test_publish_schedules_background_tasks(self) -> None:
        bus = EventBus()
        done = asyncio.Event()

        async def handler(event: DomainEvent) -> None:
            done.set()

        bus.subscribe(DocumentUploaded, handler)
        dispatched = await bus.publish(_document_event())
        assert dispatched == 1
        assert not done.is_set()
        await bus.drain()
        assert done.is_set()

    async def test_publish_returns_handler_count(self) -> None:
        bus = EventBus()
        bus.subscribe(DocumentUploaded, lambda e: None)  # noqa: E731
        bus.subscribe(None, lambda e: None)  # noqa: E731
        assert await bus.publish(_document_event()) == 2
        assert await bus.publish(_document_event()) == 2

    async def test_publish_with_no_handlers_returns_zero(self) -> None:
        bus = EventBus()
        assert await bus.publish(_document_event()) == 0

    async def test_publish_and_wait_awaits_handlers_in_order(self) -> None:
        bus = EventBus()
        ran: list[str] = []

        async def first(event: DomainEvent) -> None:
            ran.append("first")

        async def second(event: DomainEvent) -> None:
            ran.append("second")

        bus.subscribe(DocumentUploaded, first)
        bus.subscribe(DocumentUploaded, second)
        await bus.publish_and_wait(_document_event())
        assert ran == ["first", "second"]

    async def test_failing_handler_is_isolated(self) -> None:
        bus = EventBus()
        ran: list[str] = []

        async def failing(event: DomainEvent) -> None:
            raise RuntimeError("boom")

        async def healthy(event: DomainEvent) -> None:
            ran.append("healthy")

        bus.subscribe(DocumentUploaded, failing)
        bus.subscribe(DocumentUploaded, healthy)
        await bus.publish_and_wait(_document_event())
        assert ran == ["healthy"]


class TestSingleton:
    def test_get_event_bus_is_singleton(self) -> None:
        reset_event_bus()
        try:
            assert get_event_bus() is get_event_bus()
        finally:
            reset_event_bus()

    def test_reset_event_bus_replaces(self) -> None:
        reset_event_bus()
        try:
            first = get_event_bus()
            reset_event_bus()
            second = get_event_bus()
            assert first is not second
        finally:
            reset_event_bus()

