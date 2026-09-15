"""Phase 8-X X7 — API runtime metrics domain (pure, no I/O).

Authority: PO decisions of 2026-09-15 (`X7-D1`…`X7-D7`, prompt `CT-P8X-X7-GATE-02`)
implemented per ``CARBONTALLY_PHASE8X_X7_API_RUNTIME_METRICS_CONTRACT_20260915.md``.

Approved metrics only (no rate/denominator metric exists here):
request volume, HTTP status distribution, ``p95_latency_ms`` over a **rolling
60-minute** window, slow-request count (>= 1,000 ms), and error-request count
(4xx + 5xx) — attributed to **route templates**, never raw URLs.

Every value below is a PO-supplied constant (`X7-D2`…`X7-D7`) or a mechanical
derivation of one; nothing is inferred from data or tuned here.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

# --- PO-supplied values (never invented, never tuned at runtime) -------------

#: `X7-D6` — a request is slow at or above 1,000 ms.
SLOW_THRESHOLD_MS = 1000

#: `X7-D5` — rolling 60-minute latency/reporting window.
WINDOW_SECONDS = 3600

#: `X7-D2` — flush cadence (one flush at most every 5 minutes).
FLUSH_INTERVAL_SECONDS = 300

#: `X7-D2`/`X7-D5` — the slot a sample belongs to (slots make the window exact
#: and make the merge across instrumented processes a single series).
SLOT_SECONDS = 300

#: `X7-D1` — the existing generic metric store holds ONE series for X7.
SERIES_METRIC_TYPE = "API_RUNTIME"
SERIES_METRIC_NAME = "api_v3_rolling_60m"
SERIES_VERSION = 1

#: `X7-D3` — one merged series; no per-worker identity is ever written.
SERIES_SCOPE = "application_merged"

#: `X7-D7` — instrumented path prefix.
INSTRUMENTED_PREFIX = "/api/v3/"

#: Route identity used when no route template matched (a 404 or a mount).
#: The raw path is NEVER stored — it could contain identifiers.
UNMATCHED_ROUTE = "<unmatched>"

#: Latency histogram bucket upper bounds in ms (a bounded, fixed vocabulary so
#: a bucket histogram can be merged exactly across instrumented processes and
#: p95 stays computable without keeping raw samples or any PII).
BUCKET_BOUNDS_MS: tuple[int, ...] = (10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)

_STATUS_CLASSES: tuple[str, ...] = ("2xx", "3xx", "4xx", "5xx")


# --- mechanical helpers ------------------------------------------------------


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def status_class(status_code: int) -> str:
    """HTTP status class of ``status_code`` (``1xx`` collapsed into ``2xx``..``5xx``).

    Anything outside 200–599 is reported as ``5xx``: an unusual status is never
    silently dropped from the distribution.
    """
    code = int(status_code or 0)
    if 200 <= code < 300:
        return "2xx"
    if 300 <= code < 400:
        return "3xx"
    if 400 <= code < 500:
        return "4xx"
    return "5xx"


def is_slow(duration_ms: float) -> bool:
    """`X7-D6` — slow at or above the PO threshold."""
    return float(duration_ms) >= SLOW_THRESHOLD_MS


def bucket_index(duration_ms: float) -> int:
    """Index of the histogram bucket ``duration_ms`` falls into."""
    value = max(float(duration_ms), 0.0)
    for idx, bound in enumerate(BUCKET_BOUNDS_MS):
        if value < bound:
            return idx
    return len(BUCKET_BOUNDS_MS)


def bucket_upper_bound(index: int) -> Optional[int]:
    """Upper bound of a bucket (``None`` for the overflow bucket)."""
    if index < len(BUCKET_BOUNDS_MS):
        return BUCKET_BOUNDS_MS[index]
    return None


def slot_key(moment: Optional[datetime] = None) -> str:
    """Wall-clock 5-minute slot identity (UTC, ISO-8601, second precision).

    Using the wall-clock slot — not a worker identity — is what makes the
    persisted series a single **merged** series (`X7-D3`): every instrumented
    process flushing the same slot contributes to the same payload entry.

    The epoch is floored to the slot boundary, so 12:07:42 and 12:09:59 both
    belong to the 12:05 slot.
    """
    moment = moment or utcnow()
    stamp = moment.astimezone(timezone.utc)
    epoch = int(stamp.timestamp())
    floored = epoch - (epoch % SLOT_SECONDS)
    return datetime.fromtimestamp(floored, tz=timezone.utc).isoformat()


def empty_slot() -> dict[str, Any]:
    """A slot accumulator: per-route counts, status classes and histogram."""
    return {"routes": {}}


def empty_route_entry() -> dict[str, Any]:
    return {
        "requests": 0,
        "statuses": {key: 0 for key in _STATUS_CLASSES},
        "slow": 0,
        "errors": 0,
        "histogram": [0] * (len(BUCKET_BOUNDS_MS) + 1),
    }


def record_sample(
    slot: dict[str, Any],
    *,
    route: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Add one observation to a slot accumulator.

    Only the route **template**, the status class and a histogram bucket are kept
    — never a raw path, query string, body, header, token or identifier.
    """
    route_key = route or UNMATCHED_ROUTE
    routes = slot.setdefault("routes", {})
    entry = routes.get(route_key)
    if entry is None:
        entry = empty_route_entry()
        routes[route_key] = entry

    klass = status_class(status_code)
    entry["requests"] += 1
    entry["statuses"][klass] = int(entry["statuses"].get(klass, 0)) + 1
    if klass in ("4xx", "5xx"):
        entry["errors"] += 1
    if is_slow(duration_ms):
        entry["slow"] += 1
    entry["histogram"][bucket_index(duration_ms)] += 1


def prune_slots(slots: dict[str, Any], *, now: Optional[datetime] = None) -> set[str]:
    """Drop slots outside the rolling window; return the dropped slot keys."""
    moment = now or utcnow()
    cutoff = moment - timedelta(seconds=WINDOW_SECONDS)
    dropped = set()
    for key in list(slots):
        try:
            stamp = datetime.fromisoformat(key)
        except (TypeError, ValueError):
            dropped.add(key)
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if stamp < cutoff:
            dropped.add(key)
    for key in dropped:
        slots.pop(key, None)
    return dropped


def _percentile_from_histogram(histogram: Iterable[int], *, percentile: float) -> Optional[int]:
    """p95 from a merged bucket histogram (returns the bucket's upper bound).

    The value is the **upper bound of the bucket containing the p95 observation**
    (the overflow bucket reports ``None`` = "> 10,000 ms"). It is deliberately
    conservative and is reported as bucket resolution, never as an exact
    millisecond figure.
    """
    counts = [int(c or 0) for c in histogram]
    total = sum(counts)
    if total == 0:
        return None
    target = percentile / 100.0 * total
    seen = 0
    for idx, count in enumerate(counts):
        seen += count
        if seen >= target:
            return bucket_upper_bound(idx)
    return bucket_upper_bound(len(counts) - 1)


def aggregate_slots(
    slots: dict[str, Any], *, now: Optional[datetime] = None
) -> dict[str, Any]:
    """Aggregate the merged slots inside the rolling window into the payload.

    Returns the five approved metrics only — request volume, status distribution,
    ``p95_latency_ms``, slow-request count and error-request count — plus the
    per-route counts those signals are attributed to. **No rate, percentage or
    denominator-dependent figure is produced.**
    """
    moment = now or utcnow()
    window_start = moment - timedelta(seconds=WINDOW_SECONDS)

    totals: dict[str, Any] = {
        "requests": 0,
        "statuses": {key: 0 for key in _STATUS_CLASSES},
        "slow": 0,
        "errors": 0,
        "histogram": [0] * (len(BUCKET_BOUNDS_MS) + 1),
    }
    per_route: dict[str, dict[str, int]] = {}
    slots_in_window = 0

    for key in sorted(slots):
        try:
            stamp = datetime.fromisoformat(key)
        except (TypeError, ValueError):
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if stamp < window_start or stamp > moment:
            continue
        slots_in_window += 1
        payload = slots[key] or {}
        for route, entry in (payload.get("routes") or {}).items():
            requests = int(entry.get("requests") or 0)
            totals["requests"] += requests
            for klass in _STATUS_CLASSES:
                totals["statuses"][klass] += int(
                    (entry.get("statuses") or {}).get(klass, 0)
                )
            totals["slow"] += int(entry.get("slow") or 0)
            totals["errors"] += int(entry.get("errors") or 0)
            for idx, count in enumerate(entry.get("histogram") or []):
                if idx < len(totals["histogram"]):
                    totals["histogram"][idx] += int(count or 0)

            bucket = per_route.setdefault(
                route, {"requests": 0, "slow_requests": 0, "error_requests": 0}
            )
            bucket["requests"] += requests
            bucket["slow_requests"] += int(entry.get("slow") or 0)
            bucket["error_requests"] += int(entry.get("errors") or 0)

    return {
        "series": {
            "metric_type": SERIES_METRIC_TYPE,
            "metric_name": SERIES_METRIC_NAME,
            "scope": SERIES_SCOPE,
            "version": SERIES_VERSION,
        },
        "window_seconds": WINDOW_SECONDS,
        "window_start": window_start.isoformat(),
        "slots_in_window": slots_in_window,
        "request_volume": totals["requests"],
        "status_distribution": dict(totals["statuses"]),
        "p95_latency_ms": _percentile_from_histogram(totals["histogram"], percentile=95.0),
        "p95_latency_ms_resolution": "bucket_upper_bound",
        "slow_threshold_ms": SLOW_THRESHOLD_MS,
        "slow_requests": totals["slow"],
        "error_requests": totals["errors"],
        "slow_routes": {
            route: stats["slow_requests"]
            for route, stats in sorted(per_route.items())
            if stats["slow_requests"] > 0
        },
        "error_routes": {
            route: stats["error_requests"]
            for route, stats in sorted(per_route.items())
            if stats["error_requests"] > 0
        },
        "routes": dict(sorted(per_route.items())),
        "evaluated_at": moment.isoformat(),
    }

