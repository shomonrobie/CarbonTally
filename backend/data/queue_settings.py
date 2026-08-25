"""Queue settings repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``queue_settings`` row controlling review SLA defaults.
The RC2 table is a key/value store (``setting_key`` unique, ``setting_value``
jsonb) — not a flat-column row — so this repository reads/writes one JSONB
value under a fixed key and maps it onto the :class:`QueueSettings` domain
aggregate.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import QueueSettings

#: The single settings row this repository manages (RC2 key/value model).
_SETTINGS_KEY = "review_sla_defaults"


class QueueSettingsRepository(AbstractRepository[QueueSettings]):
    """Read/update the single queue-settings row (with sensible defaults)."""

    async def get_settings(self) -> QueueSettings:
        row = await self._fetch_one(
            """
            SELECT setting_key, setting_value, updated_at, updated_by
            FROM public.queue_settings
            WHERE setting_key = $1
            """,
            _SETTINGS_KEY,
        )
        if row is None:
            return QueueSettings(
                max_reviews_per_staff=5,
                sla_hours=48,
                auto_assign_enabled=True,
                escalation_hours=24,
                priority_weights={"high": 1.0, "medium": 0.6, "low": 0.3},
            )
        value = loads_jsonb(row["setting_value"]) or {}
        return QueueSettings(
            max_reviews_per_staff=int(value.get("max_reviews_per_staff") or 5),
            sla_hours=int(value.get("sla_hours") or 48),
            auto_assign_enabled=bool(value.get("auto_assign_enabled", True)),
            escalation_hours=int(value.get("escalation_hours") or 24),
            priority_weights=dict(value.get("priority_weights") or {}),
            updated_at=row.get("updated_at"),
            updated_by=row.get("updated_by"),
        )

    async def update_settings(
        self,
        max_reviews_per_staff: Optional[int],
        sla_hours: Optional[int],
        auto_assign_enabled: Optional[bool],
        escalation_hours: Optional[int],
        priority_weights: Optional[dict],
        updated_by: Optional[str],
    ) -> QueueSettings:
        current = await self.get_settings()
        new_weights = (
            dict(priority_weights)
            if priority_weights is not None
            else dict(current.priority_weights)
        )
        payload = dumps_jsonb(
            {
                "max_reviews_per_staff": (
                    max_reviews_per_staff
                    if max_reviews_per_staff is not None
                    else current.max_reviews_per_staff
                ),
                "sla_hours": sla_hours if sla_hours is not None else current.sla_hours,
                "auto_assign_enabled": (
                    auto_assign_enabled
                    if auto_assign_enabled is not None
                    else current.auto_assign_enabled
                ),
                "escalation_hours": (
                    escalation_hours
                    if escalation_hours is not None
                    else current.escalation_hours
                ),
                "priority_weights": new_weights,
            }
        )
        row = await self._fetch_one(
            """
            INSERT INTO public.queue_settings (setting_key, setting_value, updated_at, updated_by)
            VALUES ($1, $2, NOW(), $3)
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by
            RETURNING setting_key, setting_value, updated_at, updated_by
            """,
            _SETTINGS_KEY,
            payload,
            updated_by,
        )
        if row is None:
            raise RuntimeError("queue_settings upsert returned no row")
        value = loads_jsonb(row["setting_value"]) or {}
        return QueueSettings(
            max_reviews_per_staff=int(value["max_reviews_per_staff"]),
            sla_hours=int(value["sla_hours"]),
            auto_assign_enabled=bool(value["auto_assign_enabled"]),
            escalation_hours=int(value["escalation_hours"]),
            priority_weights=dict(value.get("priority_weights") or {}),
            updated_at=row.get("updated_at"),
            updated_by=row.get("updated_by"),
        )

    async def get(self, id: str):
        return await self.get_settings()

    async def save(self, entity: QueueSettings) -> QueueSettings:
        return entity

    async def delete(self, id: str) -> None:
        return None
