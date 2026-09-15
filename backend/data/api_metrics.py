"""Phase 8-X X7 — API runtime metrics persistence (existing generic metric store).

`X7-D1`: X7 metrics are persisted in the **existing** ``dashboard_metrics`` store —
no new table, no migration, no schema change. Its columns (``metric_type``,
``metric_name``, ``metric_value`` jsonb, ``period``, ``expires_at``, ``created_at``)
already support the payload.

`X7-D3`: exactly **one row** is maintained for the X7 series. Flushes from every
instrumented process merge into that row's slot map, so the persisted series is
the merged application view — never per-worker rows.

Retention: unchanged. X2's operational-metric retention prunes
``dashboard_metrics`` rows by ``created_at``; the live X7 row is refreshed on each
flush, so no retention duration, domain or semantics is altered by X7.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from data.base import dumps_jsonb, loads_jsonb
from domain.api_metrics import (
    SERIES_METRIC_NAME,
    SERIES_METRIC_TYPE,
    WINDOW_SECONDS,
    prune_slots,
)


class ApiMetricsRepository:
    """The single X7 series row inside ``dashboard_metrics``."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def merge_slots(
        self, slots: dict[str, Any], *, now: Optional[datetime] = None
    ) -> dict[str, Any]:
        """Merge ``slots`` into the one X7 series row and return the merged map.

        A row lock (``FOR UPDATE``) makes read-merge-write atomic, so two
        instrumented processes flushing concurrently can never lose a slot.
        Slots older than the rolling window are dropped on write.
        """
        moment = now or datetime.now(timezone.utc)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT id, metric_value
                    FROM public.dashboard_metrics
                    WHERE metric_type = $1 AND metric_name = $2
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT 1
                    FOR UPDATE
                    """,
                    SERIES_METRIC_TYPE,
                    SERIES_METRIC_NAME,
                )
                merged = (loads_jsonb(row["metric_value"]) if row else None) or {
                    "slots": {}
                }
                merged.setdefault("slots", {})
                _merge_slot_maps(merged["slots"], slots)
                prune_slots(merged["slots"], now=moment)
                payload = dumps_jsonb(merged)

                if row is None:
                    await conn.execute(
                        """
                        INSERT INTO public.dashboard_metrics
                            (metric_type, metric_name, metric_value, period, created_at)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        SERIES_METRIC_TYPE,
                        SERIES_METRIC_NAME,
                        payload,
                        "rolling_60m",
                        moment,
                    )
                else:
                    await conn.execute(
                        """
                        UPDATE public.dashboard_metrics
                        SET metric_value = $2, period = $3, created_at = $4
                        WHERE id = $1
                        """,
                        row["id"],
                        payload,
                        "rolling_60m",
                        moment,
                    )
        return merged["slots"]

    async def read_series(self) -> Optional[dict[str, Any]]:
        """The persisted merged series payload, or ``None`` when never flushed."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT metric_value, created_at
                FROM public.dashboard_metrics
                WHERE metric_type = $1 AND metric_name = $2
                ORDER BY created_at DESC NULLS LAST
                LIMIT 1
                """,
                SERIES_METRIC_TYPE,
                SERIES_METRIC_NAME,
            )
        if row is None:
            return None
        payload = loads_jsonb(row["metric_value"]) or {}
        payload["persisted_at"] = row["created_at"].isoformat() if row["created_at"] else None
        payload.setdefault("window_seconds", WINDOW_SECONDS)
        return payload

    async def count_series_rows(self) -> int:
        """Number of rows holding the series (must be exactly 1 after flushes)."""
        async with self._pool.acquire() as conn:
            value = await conn.fetchval(
                "SELECT count(*) FROM public.dashboard_metrics "
                "WHERE metric_type = $1 AND metric_name = $2",
                SERIES_METRIC_TYPE,
                SERIES_METRIC_NAME,
            )
        return int(value or 0)


def _merge_slot_maps(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    """Merge per-route counters/histograms of ``incoming`` into ``target``."""
    for key, payload in (incoming or {}).items():
        dest = target.setdefault(key, {"routes": {}})
        dest.setdefault("routes", {})
        for route, entry in ((payload or {}).get("routes") or {}).items():
            current = dest["routes"].get(route)
            if current is None:
                dest["routes"][route] = {
                    "requests": int(entry.get("requests") or 0),
                    "statuses": dict(entry.get("statuses") or {}),
                    "slow": int(entry.get("slow") or 0),
                    "errors": int(entry.get("errors") or 0),
                    "histogram": [int(c or 0) for c in (entry.get("histogram") or [])],
                }
                continue
            current["requests"] = int(current.get("requests") or 0) + int(
                entry.get("requests") or 0
            )
            statuses = current.setdefault("statuses", {})
            for klass, count in (entry.get("statuses") or {}).items():
                statuses[klass] = int(statuses.get(klass, 0)) + int(count or 0)
            current["slow"] = int(current.get("slow") or 0) + int(entry.get("slow") or 0)
            current["errors"] = int(current.get("errors") or 0) + int(
                entry.get("errors") or 0
            )
            hist = current.setdefault("histogram", [])
            for idx, count in enumerate(entry.get("histogram") or []):
                while len(hist) <= idx:
                    hist.append(0)
                hist[idx] = int(hist[idx] or 0) + int(count or 0)

