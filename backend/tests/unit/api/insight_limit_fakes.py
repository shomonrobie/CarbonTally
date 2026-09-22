"""In-memory stand-in for the shared Insight rate-limit store (test support).

The production store is ``data.insight_rate_limit.InsightRateLimitRepository``,
which performs each transition as one atomic SQL statement against PostgreSQL so
the allowance holds across workers. Unit tests replace it with this double, which
implements the *same* documented semantics in memory:

* a token bucket per ``(scope, key)`` with capacity ``requests_per_minute + burst``
  and a refill of ``requests_per_minute / 60`` tokens per second;
* an in-flight counter per ``(scope, key)`` bounded by ``max_concurrent``, with a
  lease expiry so a stale holder is recovered;
* denial accounting that never changes the refill basis.

LIMITATION (stated, not hidden): this double proves the *service* semantics —
ordering, allow/deny, ``Retry-After``, lease release. The atomic SQL itself can
only be verified against a disposable database, which the F-046-1 invariant
forbids by default; that verification is an integration task.
"""
from __future__ import annotations

import time
from typing import Optional


class InsightLimitsFake:
    """Deterministic, inspectable rate-limit store double."""

    def __init__(self) -> None:
        self.buckets: dict[tuple[str, str], dict[str, float]] = {}
        self.leases: dict[tuple[str, str], dict[str, float]] = {}
        self.denials: dict[tuple[str, str], int] = {}
        self.consumed: list[tuple[str, str]] = []

    # -- bucket ------------------------------------------------------------
    async def consume_token(
        self, scope: str, scope_key: str, capacity: int, refill_per_second: float
    ) -> Optional[float]:
        key = (str(scope), str(scope_key))
        now = time.monotonic()
        state = self.buckets.get(key)
        if state is None:
            state = {"tokens": float(capacity), "updated": now}
            self.buckets[key] = state
        elapsed = max(0.0, now - state["updated"])
        tokens = min(float(capacity), state["tokens"] + elapsed * float(refill_per_second))
        self.consumed.append(key)
        if tokens < 1.0:
            state["tokens"] = tokens
            state["updated"] = now
            return None
        state["tokens"] = tokens - 1.0
        state["updated"] = now
        return state["tokens"]

    async def peek_bucket(self, scope: str, scope_key: str) -> Optional[dict]:
        state = self.buckets.get((str(scope), str(scope_key)))
        if state is None:
            return None
        return {"tokens": state["tokens"], "capacity": None, "refill_per_second": None}

    async def record_denial(self, scope: str, scope_key: str) -> None:
        key = (str(scope), str(scope_key))
        self.denials[key] = self.denials.get(key, 0) + 1

    # -- leases ------------------------------------------------------------
    async def acquire_lease(
        self, scope: str, scope_key: str, max_concurrent: int, lease_seconds: int
    ) -> bool:
        key = (str(scope), str(scope_key))
        now = time.monotonic()
        state = self.leases.get(key)
        if state is None or state["expires"] <= now:
            self.leases[key] = {"in_flight": 1.0, "expires": now + lease_seconds}
            return True
        if state["in_flight"] >= float(max_concurrent):
            return False
        state["in_flight"] += 1
        state["expires"] = now + lease_seconds
        return True

    async def release_lease(self, scope: str, scope_key: str) -> None:
        key = (str(scope), str(scope_key))
        state = self.leases.get(key)
        if state is not None:
            state["in_flight"] = max(0.0, state["in_flight"] - 1)

    # -- test helpers ------------------------------------------------------
    def drain(self, scope: str, key: str) -> None:
        """Empty a bucket (simulates an exhausted allowance)."""
        self.buckets[(str(scope), str(key))] = {"tokens": 0.0, "updated": time.monotonic()}

    def seed_lease(self, scope: str, key: str, in_flight: int, lease_seconds: int = 120) -> None:
        """Pre-hold ``in_flight`` slots without going through acquire."""
        self.leases[(str(scope), str(key))] = {
            "in_flight": float(in_flight),
            "expires": time.monotonic() + lease_seconds,
        }

    def expire_lease(self, scope: str, key: str) -> None:
        """Force a stale lease (simulates a killed worker)."""
        state = self.leases.get((str(scope), str(key)))
        if state is not None:
            state["expires"] = time.monotonic() - 1
