"""Domain-events repository (Backend v2.1 §10, §14).

Append-only persistence for the RC2 ``domain_events`` table. Events are stored
as ``event_type`` + JSONB ``payload`` and reconstructed into the typed
:class:`domain.workflow.DomainEvent` subclass on read.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional, get_type_hints

from data.base import AbstractRepository, coerce_json, dumps_jsonb, loads_jsonb, to_jsonable
from domain import workflow as _workflow
from domain.workflow import DomainEvent

_EVENT_COLUMNS = """
    id, event_type, occurred_at, correlation_id, aggregate_id,
    aggregate_type, payload
"""

#: Base-class fields that are stored as columns, not inside the payload JSON.
_BASE_FIELDS = frozenset(
    {"event_id", "occurred_at", "correlation_id", "aggregate_id", "aggregate_type"}
)


def _event_registry() -> dict[str, type[DomainEvent]]:
    """Map every concrete event class name to its type (recursive walk)."""
    registry: dict[str, type[DomainEvent]] = {}
    stack: list[type[DomainEvent]] = list(DomainEvent.__subclasses__())
    while stack:
        cls = stack.pop()
        registry[cls.__name__] = cls
        stack.extend(cls.__subclasses__())
    return registry


_EVENT_CLASSES: dict[str, type[DomainEvent]] = _event_registry()


def _resolve_event_class(event_type: str) -> type[DomainEvent]:
    """Return the live event class for ``event_type``.

    ``@dataclass(..., slots=True)`` re-creates each event class to install
    ``__slots__``, leaving the pre-decorator class registered under the same
    name in ``DomainEvent.__subclasses__()``. A registry built from
    ``__subclasses__()`` can therefore capture a stale class object whose
    identity differs from the ``domain.workflow`` binding callers import.
    Resolving from the live module namespace keeps identity with callers.
    """
    candidate = getattr(_workflow, event_type, None)
    if isinstance(candidate, type) and issubclass(candidate, DomainEvent):
        return candidate
    cls = _EVENT_CLASSES.get(event_type)
    if cls is None:
        raise ValueError(f"unknown domain event type {event_type!r}")
    return cls


def _event_to_payload(event: DomainEvent) -> str:
    """Serialise the concrete event fields (excluding base columns) to JSON."""
    payload: dict[str, Any] = {}
    for field in dataclasses.fields(event):
        if field.name in _BASE_FIELDS:
            continue
        payload[field.name] = to_jsonable(getattr(event, field.name))
    return dumps_jsonb(payload)


def _event_from_row(row: Any) -> DomainEvent:
    r = dict(row)
    event_type = str(r["event_type"])
    cls = _resolve_event_class(event_type)
    payload = loads_jsonb(r.get("payload")) or {}
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        if field.name in _BASE_FIELDS:
            continue
        kwargs[field.name] = coerce_json(
            payload.get(field.name), hints.get(field.name, field.type)
        )
    return cls(
        event_id=str(r["id"]),
        occurred_at=r["occurred_at"],
        correlation_id=str(r["correlation_id"]),
        **kwargs,
    )

class EventsRepository(AbstractRepository[DomainEvent]):
    """Append-only domain-event store."""

    async def store(self, event: DomainEvent) -> DomainEvent:
        """Append one event and return it with the stored id."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.domain_events (
                event_type, occurred_at, correlation_id, aggregate_id,
                aggregate_type, payload, created_at
            ) VALUES ($1, $2, $3::uuid, $4::uuid, $5, $6::jsonb, NOW())
            RETURNING {_EVENT_COLUMNS}
            """,
            type(event).__name__,
            event.occurred_at,
            event.correlation_id,
            event.aggregate_id,
            event.aggregate_type,
            _event_to_payload(event),
        )
        if row is None:
            raise RuntimeError("domain event insert returned no row")
        return _event_from_row(row)

    async def get_by_correlation(self, correlation_id: str) -> list[DomainEvent]:
        """Return every event for one correlation, in order."""
        rows = await self._fetch_all(
            f"""
            SELECT {_EVENT_COLUMNS} FROM public.domain_events
            WHERE correlation_id = $1::uuid
            ORDER BY occurred_at, id
            """,
            correlation_id,
        )
        return [_event_from_row(r) for r in rows]

    async def replay(self, aggregate_id: str) -> list[DomainEvent]:
        """Replay every event for one aggregate, in order."""
        rows = await self._fetch_all(
            f"""
            SELECT {_EVENT_COLUMNS} FROM public.domain_events
            WHERE aggregate_id = $1::uuid
            ORDER BY occurred_at, id
            """,
            aggregate_id,
        )
        return [_event_from_row(r) for r in rows]

    async def get(self, id: str) -> Optional[DomainEvent]:
        """Return the single event with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_EVENT_COLUMNS} FROM public.domain_events WHERE id = $1",
            id,
        )
        return _event_from_row(row) if row is not None else None

    async def save(self, entity: DomainEvent) -> DomainEvent:
        """Persist an event (append-only: ``save`` inserts)."""
        return await self.store(entity)

    async def delete(self, id: str) -> None:
        """Delete an event (not used — events are immutable)."""
        await self._execute(
            "DELETE FROM public.domain_events WHERE id = $1", id
        )

