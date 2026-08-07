"""Decorator-based audit logging (Backend v2.1 §15 Audit Framework).

``AuditLogger`` wraps an append-only audit sink (the
:class:`data.audit.AuditRepository` in production, an in-memory stub in unit
tests) and adds:

* :meth:`log_action` — record one action with full context, and
* :meth:`audit` — an async decorator that records an entry around an operation:
  success entries capture the action plus optional before/after state; failures
  are recorded with the exception as the reason and re-raised.

The decorator never raises from its own recording — audit failures are logged,
never allowed to break the wrapped operation, and entries without a resolvable
entity context are skipped.

Dependency rules: this module imports from ``core`` (logging), the ``domain``
package (audit types), the repository layer (the sink) and ``infra.supabase``
(the singleton pool). No business logic lives here.
"""
from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional, ParamSpec, Protocol, TypeVar, Union

from core.logging import get_logger
from data.audit import AuditRepository
from data.base import to_jsonable
from domain.audit import AuditEntry, AuditQuery
from infra.supabase import get_service_pool

P = ParamSpec("P")
R = TypeVar("R")

logger = get_logger(__name__)

#: A before-snapshot: a static dict, or a callable receiving the wrapped
#: function's ``(*args, **kwargs)`` and returning the snapshot dict.
BeforeState = Union[dict[str, Any], Callable[..., dict[str, Any]]]


class AuditSink(Protocol):
    """The persistence contract ``AuditLogger`` records against."""

    async def record(self, entry: AuditEntry) -> AuditEntry: ...

    async def query(self, filters: AuditQuery) -> list[AuditEntry]: ...


class AuditLogger:
    """Records audit entries around engine operations.

    Args:
        sink: Append-only audit persistence (an ``AuditRepository``).
        default_actor: Actor used when a recorded action has no actor.
    """

    def __init__(self, sink: AuditSink, *, default_actor: str = "system") -> None:
        self._sink = sink
        self._default_actor = default_actor

    @property
    def default_actor(self) -> str:
        """The actor applied to actions that do not supply one."""
        return self._default_actor

    async def record(self, entry: AuditEntry) -> AuditEntry:
        """Persist ``entry`` and return it with the stored id."""
        return await self._sink.record(entry)

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        """Search the audit trail through the configured sink."""
        return await self._sink.query(filters)

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: Optional[str] = None,
        changed_fields: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> AuditEntry:
        """Build and persist one audit entry."""
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or self._default_actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields=dict(changed_fields or {}),
            reason=reason,
            ip_address=ip_address,
            before=before,
            after=after,
        )
        return await self._sink.record(entry)

    def audit(
        self,
        *,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_type_arg: Optional[str] = None,
        entity_id_arg: Optional[str] = None,
        actor: Optional[str] = None,
        actor_arg: Optional[str] = None,
        correlation_id: Optional[str] = None,
        correlation_id_arg: Optional[str] = None,
        before: Optional[BeforeState] = None,
        record_result: bool = False,
        record_failures: bool = True,
    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
        """Decorate an async function so every call is audited.

        Arg-derived fields name parameters of the wrapped function
        (``entity_id_arg="document_id"`` reads the ``document_id`` parameter).
        ``action`` defaults to the wrapped function's name. On success the
        entry is recorded with optional ``before``/``after`` snapshots; on
        failure the exception is recorded as the ``reason`` and re-raised
        (unless ``record_failures`` is ``False``).
        """

        def decorate(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                bound = inspect.signature(func).bind_partial(*args, **kwargs)
                action_name = action or func.__name__
                resolved_entity_type = entity_type or _resolve_arg(
                    entity_type_arg, bound
                )
                resolved_entity_id = _resolve_arg(entity_id_arg, bound)
                resolved_actor = (
                    actor or _resolve_arg(actor_arg, bound) or self._default_actor
                )
                resolved_correlation = (
                    correlation_id
                    or _resolve_arg(correlation_id_arg, bound)
                    or str(uuid.uuid4())
                )
                before_state = _resolve_before(before, args, kwargs)
                try:
                    result = await func(*args, **kwargs)
                except Exception as exc:
                    if record_failures:
                        await self._try_record(
                            action=action_name,
                            entity_type=resolved_entity_type,
                            entity_id=resolved_entity_id,
                            actor=resolved_actor,
                            correlation_id=resolved_correlation,
                            reason=f"{type(exc).__name__}: {exc}",
                            before=before_state,
                        )
                    raise
                after_state = to_jsonable(result) if record_result else None
                await self._try_record(
                    action=action_name,
                    entity_type=resolved_entity_type,
                    entity_id=resolved_entity_id,
                    actor=resolved_actor,
                    correlation_id=resolved_correlation,
                    before=before_state,
                    after=after_state,
                )
                return result

            return wrapper

        return decorate

    async def _try_record(
        self,
        *,
        action: str,
        entity_type: Any,
        entity_id: Any,
        actor: str,
        correlation_id: str,
        reason: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> None:
        """Record an entry best-effort; never raise into the wrapped operation."""
        if not entity_type or not entity_id:
            return
        try:
            await self.log_action(
                action=action,
                entity_type=str(entity_type),
                entity_id=str(entity_id),
                correlation_id=correlation_id,
                actor=actor,
                reason=reason,
                before=before,
                after=after,
            )
        except Exception:  # noqa: BLE001 - audit must not break the caller
            logger.exception(
                "failed to record audit entry for %s %s", entity_type, entity_id
            )


def _resolve_arg(name: Optional[str], bound: inspect.BoundArguments) -> Any:
    """Return the bound value of parameter ``name``, or ``None``."""
    if name is None:
        return None
    return bound.arguments.get(name)


def _resolve_before(
    before: Optional[BeforeState],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Resolve a before-snapshot (static dict or callable) to JSON-safe data."""
    if before is None:
        return None
    if callable(before):
        return to_jsonable(before(*args, **kwargs))
    return to_jsonable(before)


_audit_logger: Optional[AuditLogger] = None


def init_audit_logger(sink: AuditSink, *, default_actor: str = "system") -> AuditLogger:
    """Install and return the process-wide audit logger (used by tests/DI)."""
    global _audit_logger
    _audit_logger = AuditLogger(sink, default_actor=default_actor)
    return _audit_logger


async def get_audit_logger() -> AuditLogger:
    """Return the process-wide audit logger, creating one over the service pool."""
    global _audit_logger
    if _audit_logger is None:
        pool = await get_service_pool()
        _audit_logger = AuditLogger(AuditRepository(pool))
    return _audit_logger


def reset_audit_logger() -> None:
    """Drop the cached audit logger (used by test suites)."""
    global _audit_logger
    _audit_logger = None

