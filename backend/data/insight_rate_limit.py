"""CarbonTally Insight — database-backed rate-limit state (Phase 8 I8-A).

Authorization: PO Insight Discovery-Aggregation-Provenance-RateLimiting package
(2026-09-22) — *technical abuse protection only*. This module carries **no**
commercial meaning: no plan, entitlement, credit, overage, quota or billing
concept exists here, and none may be derived from it.

Why the database rather than process memory: the application runs behind a
multi-worker server, so a per-process counter would let a caller multiply its
allowance by the number of workers. These two tables are the narrowest existing
store (the service-role PostgreSQL pool the whole data layer already uses), and
every mutation is a **single atomic statement** so concurrent workers cannot
interleave read/modify/write.

State:
* ``insight_rate_limit_buckets`` — a token bucket per (scope, key): sustained
  ``requests_per_minute`` with a bounded ``burst`` allowance after idle;
* ``insight_concurrency_leases`` — an in-flight counter per (scope, key) with a
  lease expiry, so a crashed worker cannot permanently hold capacity.

Only counters and timestamps are stored. No question text, no identifiers of
customer data, no provider output.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

#: Consume one token atomically. The refill is derived from the row's own
#: ``updated_at`` inside the same statement, so two workers cannot both consume
#: the same token or both refill from the same elapsed interval.
_CONSUME_SQL = """
INSERT INTO public.insight_rate_limit_buckets AS b
    (scope, scope_key, tokens, capacity, refill_per_second, updated_at)
VALUES ($1, $2, $3 - 1, $3, $4, now())
ON CONFLICT (scope, scope_key) DO UPDATE SET
    tokens = LEAST($3, b.tokens + EXTRACT(EPOCH FROM (now() - b.updated_at)) * $4) - 1,
    capacity = $3,
    refill_per_second = $4,
    updated_at = now()
WHERE LEAST($3, b.tokens + EXTRACT(EPOCH FROM (now() - b.updated_at)) * $4) >= 1
RETURNING tokens
"""

#: Best-effort read of the bucket for a truthful ``Retry-After`` hint.
_PEEK_SQL = """
SELECT tokens, capacity, refill_per_second
  FROM public.insight_rate_limit_buckets
 WHERE scope = $1 AND scope_key = $2
"""

#: Observability only: a denial is counted on the existing row. ``updated_at`` is
#: deliberately NOT touched, because it is the refill basis.
_RECORD_DENIAL_SQL = """
UPDATE public.insight_rate_limit_buckets
   SET denied_count = denied_count + 1, last_denied_at = now()
 WHERE scope = $1 AND scope_key = $2
"""

#: Acquire one in-flight slot. An expired lease is recovered (stale-lock
#: recovery), otherwise the in-flight count must still be below the ceiling.
_ACQUIRE_LEASE_SQL = """
INSERT INTO public.insight_concurrency_leases AS c
    (scope, scope_key, in_flight, max_concurrent, lease_expires_at, updated_at)
VALUES ($1, $2, 1, $3, now() + make_interval(secs => $4), now())
ON CONFLICT (scope, scope_key) DO UPDATE SET
    in_flight = CASE
        WHEN c.lease_expires_at IS NULL OR c.lease_expires_at <= now() THEN 1
        ELSE c.in_flight + 1
    END,
    max_concurrent = $3,
    lease_expires_at = now() + make_interval(secs => $4),
    updated_at = now()
WHERE c.lease_expires_at IS NULL
   OR c.lease_expires_at <= now()
   OR c.in_flight < $3
RETURNING in_flight
"""

_RELEASE_LEASE_SQL = """
UPDATE public.insight_concurrency_leases
   SET in_flight = GREATEST(in_flight - 1, 0), updated_at = now()
 WHERE scope = $1 AND scope_key = $2
"""


class InsightRateLimitRepository(AbstractRepository):
    """Atomic counter store for the Insight execution rate limiter."""

    async def consume_token(
        self, scope: str, scope_key: str, capacity: int, refill_per_second: float
    ) -> Optional[float]:
        """Consume one token.

        Returns the remaining token count (float) when the request is admitted,
        or ``None`` when the bucket is empty (the caller is over the limit).
        """
        row = await self._fetch_one(
            _CONSUME_SQL,
            str(scope),
            str(scope_key),
            int(capacity),
            float(refill_per_second),
        )
        return float(row["tokens"]) if row is not None else None

    async def peek_bucket(self, scope: str, scope_key: str) -> Optional[dict[str, Any]]:
        """Read the current bucket state (used only to compute ``Retry-After``)."""
        row = await self._fetch_one(_PEEK_SQL, str(scope), str(scope_key))
        return dict(row) if row is not None else None

    async def record_denial(self, scope: str, scope_key: str) -> None:
        """Count a denial for observability (never changes the refill basis)."""
        await self._execute(_RECORD_DENIAL_SQL, str(scope), str(scope_key))

    async def acquire_lease(
        self, scope: str, scope_key: str, max_concurrent: int, lease_seconds: int
    ) -> bool:
        """Acquire one in-flight slot; ``False`` means the concurrency ceiling holds."""
        row = await self._fetch_one(
            _ACQUIRE_LEASE_SQL,
            str(scope),
            str(scope_key),
            int(max_concurrent),
            float(lease_seconds),
        )
        return row is not None

    async def release_lease(self, scope: str, scope_key: str) -> None:
        """Release one in-flight slot (idempotent; never goes below zero)."""
        await self._execute(_RELEASE_LEASE_SQL, str(scope), str(scope_key))

    async def get(self, entity_id: str):  # pragma: no cover - boundary
        raise NotImplementedError(
            "Insight rate-limit state has no entity read surface; use "
            "peek_bucket(scope, scope_key)."
        )

    async def save(self, entity):  # pragma: no cover - boundary
        raise NotImplementedError(
            "Insight rate-limit state is mutated only through the atomic "
            "consume_token / acquire_lease / release_lease statements."
        )

    async def delete(self, entity_id: str) -> None:  # pragma: no cover - guard
        raise NotImplementedError(
            "Insight rate-limit rows are operational counters and are not deleted here."
        )
