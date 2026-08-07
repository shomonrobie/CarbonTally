"""Repository base class and shared row-mapping helpers (Backend v2.1 §10).

``AbstractRepository`` is the generic contract every repository implements. The
module-level JSON helpers are shared by the repositories that persist JSONB
columns (import errors, audit payloads, domain-event payloads, log metadata).
"""
from __future__ import annotations

import datetime
import json
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar, cast, get_args, get_origin

import asyncpg

T = TypeVar("T")

#: Types that survive ``json.dumps`` without conversion.
_JSON_SAFE = (str, int, float, bool, type(None))


class AbstractRepository(ABC, Generic[T]):
    """Generic repository contract.

    Args:
        pool: The service-role ``asyncpg`` pool used for all persistence.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        if pool is None:
            raise ValueError("pool must not be None")
        self._pool = pool

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Return the entity with ``id``, or ``None`` when it does not exist."""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Persist ``entity`` (insert or update) and return the stored state."""

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Remove the entity with ``id`` (no-op when it does not exist)."""

    async def _fetch_one(
        self, query: str, *args: Any
    ) -> Optional[asyncpg.Record]:
        """Run ``query`` and return the first row, or ``None``."""
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def _fetch_all(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Run ``query`` and return every row."""
        async with self._pool.acquire() as conn:
            return list(await conn.fetch(query, *args))

    async def _execute(self, query: str, *args: Any) -> str:
        """Execute a write statement and return its status."""
        async with self._pool.acquire() as conn:
            return cast(str, await conn.execute(query, *args))


# ---------------------------------------------------------------------------
# JSONB round-tripping helpers
# ---------------------------------------------------------------------------


def to_jsonable(value: Any) -> Any:
    """Convert a domain value into a ``json``-serialisable structure.

    Handles :class:`decimal.Decimal`, :class:`datetime.date`,
    :class:`datetime.datetime`, :class:`uuid.UUID`, tuples and ``None``.
    """
    if value is None or isinstance(value, _JSON_SAFE):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return str(value)


def dumps_jsonb(value: Any) -> str:
    """Serialise a domain value to a JSON string for a JSONB column."""
    return json.dumps(to_jsonable(value), separators=(",", ":"))


def loads_jsonb(raw: Any) -> Any:
    """Parse a JSONB value (string, dict or list) back to Python objects."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    return json.loads(raw)


def coerce_json(value: Any, target: type[Any]) -> Any:
    """Coerce a JSON-decoded value to the target type.

    Used to reconstruct typed domain objects from JSONB payloads. Supports
    ``Optional[X]``, ``tuple[X, ...]``, ``Decimal``, ``datetime``/``date`` and
    primitive types.
    """
    origin = get_origin(target)
    if origin is None:
        return _coerce_scalar(value, target)
    if origin in (tuple, list):
        args = get_args(target)
        elem = args[0] if args else Any
        if value is None:
            return ()
        items = value if isinstance(value, (list, tuple)) else [value]
        converted = [coerce_json(item, elem) for item in items]
        return tuple(converted) if origin is tuple else converted
    if origin is dict:
        args = get_args(target)
        vtype = args[1] if len(args) > 1 else Any
        if not isinstance(value, dict):
            return {}
        return {str(key): coerce_json(item, vtype) for key, item in value.items()}
    if str(origin).startswith("typing.Union"):
        if value is None:
            return None
        for arg in get_args(target):
            if arg is type(None):
                continue
            return coerce_json(value, arg)
    return _coerce_scalar(value, target)


def _coerce_scalar(value: Any, target: type[Any]) -> Any:
    if value is None:
        return None
    if target is Any or target is object:
        return value
    if target is str:
        return value if isinstance(value, str) else str(value)
    if target is int:
        return int(value)
    if target is float:
        return float(value)
    if target is bool:
        return bool(value)
    if target is Decimal:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    if target is datetime.datetime:
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value)
        return value
    if target is datetime.date:
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, str):
            return datetime.date.fromisoformat(value)
        return value
    return value

