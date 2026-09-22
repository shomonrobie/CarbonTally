"""CarbonTally Insight — execution rate limiting (Phase 8 I8-A, technical only).

Authorization: PO Insight Discovery-Aggregation-Provenance-RateLimiting package
(2026-09-22). Scope, exactly:

* **technical abuse protection** for customer-facing Insight execution;
* server-controlled, environment-configurable defaults; a client can never raise
  its own limit because no request field participates in the decision;
* per authenticated user *and* per organisation, plus bounded concurrency;
* HTTP ``429`` with ``Retry-After`` when refused, before expensive work (tool
  execution, provider narration) happens;
* the existing I4 ``rate_limited`` answer state is used where a Layer-2 record
  exists to carry it (the interaction path).

Explicitly NOT in this module: commercial plans, entitlements, credits,
overages, quotas, payment processing, model-token accounting, I7 retention or
full I8. Nothing here may be reused as a billing signal.

The limiter state is shared (PostgreSQL) and every transition is one atomic
statement, so the allowance holds across workers and instances.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:  # pragma: no cover - type-only
    from api.dependencies import RepositoryBundle

logger = logging.getLogger(__name__)

SCOPE_USER = "user"
SCOPE_ORG = "org"

#: Environment controls (server-side only; never request-derived).
ENV_ENABLED = "CARBONTALLY_INSIGHT_RATE_LIMIT_ENABLED"
ENV_USER_PER_MINUTE = "CARBONTALLY_INSIGHT_RATE_LIMIT_USER_PER_MINUTE"
ENV_USER_BURST = "CARBONTALLY_INSIGHT_RATE_LIMIT_USER_BURST"
ENV_USER_MAX_CONCURRENT = "CARBONTALLY_INSIGHT_RATE_LIMIT_USER_MAX_CONCURRENT"
ENV_ORG_PER_MINUTE = "CARBONTALLY_INSIGHT_RATE_LIMIT_ORG_PER_MINUTE"
ENV_ORG_BURST = "CARBONTALLY_INSIGHT_RATE_LIMIT_ORG_BURST"
ENV_ORG_MAX_CONCURRENT = "CARBONTALLY_INSIGHT_RATE_LIMIT_ORG_MAX_CONCURRENT"

#: Maximum in-flight duration a lease may be held before it is reclaimed.
LEASE_SECONDS = 120
#: A refusal never advertises a wait longer than this.
MAX_RETRY_AFTER_SECONDS = 120


@dataclass(frozen=True, slots=True)
class InsightRateLimitPolicy:
    """One bounded rate-limit policy (sustained rate, burst credit, concurrency)."""

    name: str
    requests_per_minute: int
    burst: int
    max_concurrent: int

    @property
    def capacity(self) -> int:
        """Bucket capacity = sustained allowance + burst credit."""
        return self.requests_per_minute + self.burst

    @property
    def refill_per_second(self) -> float:
        return self.requests_per_minute / 60.0


#: Ratified security defaults (not commercial entitlements).
DEFAULT_USER_POLICY = InsightRateLimitPolicy(SCOPE_USER, 20, 5, 2)
DEFAULT_ORG_POLICY = InsightRateLimitPolicy(SCOPE_ORG, 100, 20, 10)

#: Safety ceilings: an operator may tune down (or up to these), never unbounded.
USER_CEILING = (600, 100, 20)
ORG_CEILING = (6_000, 1_000, 100)


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """The outcome of one rate-limit check (never a grant of authorization)."""

    allowed: bool
    scope: Optional[str] = None
    limit: int = 0
    capacity: int = 0
    remaining: int = 0
    retry_after_seconds: int = 0
    enforced: bool = True


@dataclass(frozen=True, slots=True)
class ExecutionLease:
    """Acquired concurrency slots, with everything needed to release them."""

    acquired: bool
    scope: Optional[str] = None
    max_concurrent: int = 0
    retry_after_seconds: int = 0
    keys: tuple[tuple[str, str], ...] = ()

    @property
    def held(self) -> bool:
        return bool(self.keys)


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read a bounded integer from the environment (invalid values fall back)."""
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("%s is not an integer; using the ratified default", name)
        return default
    if value < minimum or value > maximum:
        logger.warning(
            "%s=%s is outside %s..%s; using the ratified default",
            name,
            value,
            minimum,
            maximum,
        )
        return default
    return value


def configured_policies() -> tuple[InsightRateLimitPolicy, InsightRateLimitPolicy]:
    """The effective policies (ratified defaults, or bounded operator overrides)."""
    user = InsightRateLimitPolicy(
        SCOPE_USER,
        _int_env(
            ENV_USER_PER_MINUTE, DEFAULT_USER_POLICY.requests_per_minute, 1, USER_CEILING[0]
        ),
        _int_env(ENV_USER_BURST, DEFAULT_USER_POLICY.burst, 0, USER_CEILING[1]),
        _int_env(
            ENV_USER_MAX_CONCURRENT, DEFAULT_USER_POLICY.max_concurrent, 1, USER_CEILING[2]
        ),
    )
    org = InsightRateLimitPolicy(
        SCOPE_ORG,
        _int_env(
            ENV_ORG_PER_MINUTE, DEFAULT_ORG_POLICY.requests_per_minute, 1, ORG_CEILING[0]
        ),
        _int_env(ENV_ORG_BURST, DEFAULT_ORG_POLICY.burst, 0, ORG_CEILING[1]),
        _int_env(
            ENV_ORG_MAX_CONCURRENT, DEFAULT_ORG_POLICY.max_concurrent, 1, ORG_CEILING[2]
        ),
    )
    return user, org


def rate_limiting_enabled() -> bool:
    """Whether enforcement is active (default: active; env can only be explicit)."""
    raw = (os.getenv(ENV_ENABLED) or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        logger.warning(
            "Insight rate limiting is disabled by %s (the PO default is enabled)",
            ENV_ENABLED,
        )
        return False
    return True


def _key_digest(value: str) -> str:
    """A short, non-reversible correlation digest for logs (no raw identifiers)."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _retry_after_from_bucket(
    bucket: Optional[dict[str, Any]], policy: InsightRateLimitPolicy
) -> int:
    """Seconds until one token is available, from the bucket's own refill rate."""
    tokens = 0.0
    refill = policy.refill_per_second
    if bucket:
        try:
            tokens = float(bucket.get("tokens") or 0.0)
            refill = float(bucket.get("refill_per_second") or refill)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            tokens, refill = 0.0, policy.refill_per_second
    if refill <= 0:  # pragma: no cover - defensive
        return MAX_RETRY_AFTER_SECONDS
    seconds = int(math.ceil(max(1.0 - tokens, 0.0) / refill))
    return max(1, min(seconds, MAX_RETRY_AFTER_SECONDS))


async def check_request_rates(
    *,
    repos: "RepositoryBundle",
    user_id: str,
    organization_id: str,
) -> RateLimitDecision:
    """Consume one token for the authenticated user and, second, for the organisation.

    Both scopes are always evaluated in a fixed order (user then org), so the
    decision is deterministic and the organisation ceiling holds even when many
    users act at once. The caller's authenticated identity is the only input — no
    request field can raise a limit.
    """
    if not rate_limiting_enabled():
        return RateLimitDecision(allowed=True, enforced=False)
    user_policy, org_policy = configured_policies()
    store = repos.insight_limits
    last = RateLimitDecision(allowed=True, enforced=True)
    for policy, key in ((user_policy, user_id), (org_policy, organization_id)):
        remaining = await store.consume_token(
            policy.name, key, policy.capacity, policy.refill_per_second
        )
        if remaining is None:
            try:
                await store.record_denial(policy.name, key)
            except Exception:  # noqa: BLE001 - accounting must never decide access
                logger.warning("insight rate-limit denial accounting failed")
            bucket = await store.peek_bucket(policy.name, key)
            retry_after = _retry_after_from_bucket(bucket, policy)
            logger.warning(
                "insight rate limit denied scope=%s key=%s retry_after=%ss",
                policy.name,
                _key_digest(key),
                retry_after,
            )
            return RateLimitDecision(
                allowed=False,
                scope=policy.name,
                limit=policy.requests_per_minute,
                capacity=policy.capacity,
                remaining=0,
                retry_after_seconds=retry_after,
            )
        last = RateLimitDecision(
            allowed=True,
            scope=policy.name,
            limit=policy.requests_per_minute,
            capacity=policy.capacity,
            remaining=max(0, min(int(remaining), policy.capacity)),
            retry_after_seconds=0,
        )
    return last


async def acquire_execution_leases(
    *,
    repos: "RepositoryBundle",
    user_id: str,
    organization_id: str,
) -> ExecutionLease:
    """Acquire the per-user and per-organisation in-flight slots.

    A denial is not an error: the caller decides how to answer it (the
    interaction path records ``rate_limited`` evidence and answers 429).
    """
    if not rate_limiting_enabled():
        return ExecutionLease(acquired=True, keys=())
    user_policy, org_policy = configured_policies()
    store = repos.insight_limits
    held: list[tuple[str, str]] = []
    for policy, key in ((user_policy, user_id), (org_policy, organization_id)):
        acquired = await store.acquire_lease(
            policy.name, key, policy.max_concurrent, LEASE_SECONDS
        )
        if not acquired:
            await release_execution_leases(
                repos=repos, lease=ExecutionLease(acquired=True, keys=tuple(held))
            )
            logger.warning(
                "insight concurrency limit reached scope=%s key=%s",
                policy.name,
                _key_digest(key),
            )
            return ExecutionLease(
                acquired=False,
                scope=policy.name,
                max_concurrent=policy.max_concurrent,
                retry_after_seconds=LEASE_SECONDS,
            )
        held.append((policy.name, key))
    return ExecutionLease(acquired=True, keys=tuple(held))


async def release_execution_leases(
    *, repos: "RepositoryBundle", lease: Optional[ExecutionLease]
) -> None:
    """Release every slot the caller still holds (safe on any path)."""
    if lease is None or not lease.keys:
        return
    for scope, key in lease.keys:
        try:
            await repos.insight_limits.release_lease(scope, key)
        except Exception:  # noqa: BLE001 - a stale lease expires on its own
            logger.warning("insight concurrency lease release failed scope=%s", scope)


def rate_limit_headers(decision: RateLimitDecision) -> dict[str, str]:
    """Informational headers for an admitted request."""
    if not decision.enforced:
        return {}
    return {
        "X-RateLimit-Limit": str(decision.limit),
        "X-RateLimit-Remaining": str(max(0, decision.remaining)),
        "X-RateLimit-Reset": str(max(1, decision.retry_after_seconds or 60)),
    }


def refusal_headers(retry_after_seconds: int) -> dict[str, str]:
    """Headers for a ``429`` refusal (``Retry-After`` is the operative one)."""
    seconds = max(1, min(int(retry_after_seconds or 1), MAX_RETRY_AFTER_SECONDS))
    return {
        "Retry-After": str(seconds),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(seconds),
    }


def rate_limited_error(decision: RateLimitDecision) -> HTTPException:
    """The truthful refusal: an HTTP ``429``, never a fabricated answer state."""
    target = "your account" if decision.scope == SCOPE_USER else "your organisation"
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Insight request limit reached for {target}. Wait and try again.",
        headers=refusal_headers(decision.retry_after_seconds),
    )
