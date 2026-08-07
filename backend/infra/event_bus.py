"""In-process publish/subscribe event bus (Backend v2.1 §14, §4.3).

The infrastructure side of the Workflow & Event Platform: a process-local
pub/sub used for **fire-and-forget side effects**. Engines publish
:class:`domain.workflow.DomainEvent` instances; handlers registered at startup
react to them (persisting to ``domain_events``, refreshing the search index,
driving workflow transitions).

Publishing never awaits handler completion — each dispatch is scheduled as a
background task so a slow side effect can never block the publisher. The bus
exposes :meth:`drain` (wait for in-flight tasks) and :meth:`publish_and_wait`
(deterministic in-order delivery) for tests and orderly shutdown. A failing
handler is logged and isolated: it never breaks the publisher or other handlers.

Dependency rules: this module imports only from ``core`` (logging) and
``domain`` (the event type) — it contains no business logic.
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Callable, Optional

from core.logging import get_logger
from domain.workflow import DomainEvent

logger = get_logger(__name__)

#: Key under which wildcard (all-events) handlers are registered.
_WILDCARD = "*"

#: A handler receives one event and may be synchronous or asynchronous.
EventHandler = Callable[[DomainEvent], object]


class EventBus:
    """Process-local publish/subscribe bus for domain events.

    Args:
        max_handlers: Maximum number of handlers for any single event type
            (including the wildcard bucket); guards against runaway growth.
    """

    def __init__(self, max_handlers: int = 100) -> None:
        if max_handlers < 1:
            raise ValueError("max_handlers must be >= 1")
        self._max_handlers = max_handlers
        self._handlers: dict[str, list[EventHandler]] = {_WILDCARD: []}
        self._tasks: set[asyncio.Task[None]] = set()

    @property
    def max_handlers(self) -> int:
        """The configured per-type handler limit."""
        return self._max_handlers

    def subscribe(
        self, event_type: Optional[type[DomainEvent]], handler: EventHandler
    ) -> None:
        """Register ``handler`` for ``event_type`` (or all events when ``None``).

        Raises:
            ValueError: When ``handler`` is already subscribed to that type, or
                when the type's handler bucket is full.
        """
        key = event_type.__name__ if event_type is not None else _WILDCARD
        bucket = self._handlers.setdefault(key, [])
        if len(bucket) >= self._max_handlers:
            raise ValueError(
                f"too many handlers registered for {key!r} "
                f"(limit {self._max_handlers})"
            )
        if handler in bucket:
            raise ValueError(f"handler {handler!r} is already subscribed to {key!r}")
        bucket.append(handler)

    def unsubscribe(
        self, event_type: Optional[type[DomainEvent]], handler: EventHandler
    ) -> bool:
        """Remove ``handler``; return ``True`` when it was registered."""
        key = event_type.__name__ if event_type is not None else _WILDCARD
        bucket = self._handlers.get(key)
        if not bucket:
            return False
        try:
            bucket.remove(handler)
        except ValueError:
            return False
        return True

    def subscriber_count(
        self, event_type: Optional[type[DomainEvent]] = None
    ) -> int:
        """Return the number of handlers for ``event_type`` (or total when None)."""
        if event_type is None:
            return sum(len(bucket) for bucket in self._handlers.values())
        return len(self._handlers.get(event_type.__name__, []))

    def clear(self) -> None:
        """Drop every registered handler and discard in-flight tasks."""
        self._handlers = {_WILDCARD: []}
        self._tasks.clear()

    async def publish(self, event: DomainEvent) -> int:
        """Dispatch ``event`` to every matching handler as background tasks.

        Requires a running event loop. Returns the number of handlers
        dispatched; delivery is asynchronous — await :meth:`drain` to wait.
        """
        handlers = self._matching_handlers(type(event).__name__)
        for handler in handlers:
            task = asyncio.create_task(self._invoke(handler, event))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        return len(handlers)

    async def publish_and_wait(self, event: DomainEvent) -> int:
        """Dispatch ``event`` and await every handler, in registration order.

        Handlers still run in the caller's task (sequential semantics); this is
        the deterministic path used by tests and request-scoped consumers.
        """
        handlers = self._matching_handlers(type(event).__name__)
        for handler in handlers:
            await self._invoke(handler, event)
        return len(handlers)

    async def drain(self) -> None:
        """Wait for every in-flight background dispatch to finish."""
        if not self._tasks:
            return
        await asyncio.gather(*self._tasks, return_exceptions=True)

    def _matching_handlers(self, event_name: str) -> list[EventHandler]:
        return list(self._handlers.get(event_name, [])) + list(
            self._handlers[_WILDCARD]
        )

    async def _invoke(self, handler: EventHandler, event: DomainEvent) -> None:
        try:
            result = handler(event)
            if inspect.isawaitable(result):
                await result
        except Exception:  # noqa: BLE001 - a handler must never break the bus
            logger.exception(
                "event handler %r failed for event %s",
                handler,
                type(event).__name__,
            )


_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Return the process-wide event bus (singleton)."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def reset_event_bus() -> None:
    """Drop the cached bus (used by test suites)."""
    global _bus
    _bus = None
