"""Platform settings repository (N3 retention + Analytics & Integrations).

Retention is a CONFIGURABLE product capability (N3). The RC2
``system_settings`` table already carries the retention columns
(``audit_log_retention_days``, ``data_retention_days``,
``document_retention_days``, ``backup_retention_days``) — this repository reads
and writes those columns and never invents policy values: unset values are
returned as ``None`` so the UI shows "not configured" rather than a fabricated
duration.

Analytics & Integrations provider configuration is stored in the same
``system_settings`` table under its own ``setting_key`` and in the table's
generic ``setting_value`` JSONB column. No provider-specific table is created,
and only Google Analytics 4 is implemented.
"""

from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb

#: Fixed key for the single system_settings row this repository manages.
_SETTINGS_KEY = "platform_retention"

_RETENTION_COLUMNS = (
    "audit_log_retention_days, data_retention_days, document_retention_days, "
    "backup_retention_days, operational_telemetry_retention_days, updated_at, updated_by"
)

#: Fixed key for the Analytics & Integrations configuration row (GA4 only).
_ANALYTICS_KEY = "analytics_ga4"

_ANALYTICS_COLUMNS = "setting_value, updated_at, updated_by"


def _analytics_from_row(row: Optional[Any]) -> dict:
    """Map a ``system_settings`` row to the analytics configuration shape.

    A missing row, an unparseable payload or a malformed value fails closed:
    analytics is reported as disabled with no measurement ID, and the public
    configuration read never raises on stored data.
    """
    try:
        value = loads_jsonb(row.get("setting_value")) if row is not None else None
    except (TypeError, ValueError):
        value = None
    if not isinstance(value, dict):
        value = {}
    measurement_id = value.get("ga4_measurement_id")
    if not isinstance(measurement_id, str) or not measurement_id.strip():
        measurement_id = None
    return {
        "enabled": bool(value.get("enabled", False)),
        "ga4_measurement_id": measurement_id,
        "updated_at": row.get("updated_at") if row is not None else None,
        "updated_by": row.get("updated_by") if row is not None else None,
    }


class SettingsRepository(AbstractRepository[dict]):
    """Read/update the platform settings rows (retention + analytics)."""

    async def get_retention(self) -> dict:
        row = await self._fetch_one(
            f"""
            SELECT {_RETENTION_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _SETTINGS_KEY,
        )
        if row is None:
            return {
                "audit_log_retention_days": None,
                "data_retention_days": None,
                "document_retention_days": None,
                "backup_retention_days": None,
                "operational_telemetry_retention_days": None,
                "updated_at": None,
                "updated_by": None,
            }
        return {
            "audit_log_retention_days": row.get("audit_log_retention_days"),
            "data_retention_days": row.get("data_retention_days"),
            "document_retention_days": row.get("document_retention_days"),
            "backup_retention_days": row.get("backup_retention_days"),
            "operational_telemetry_retention_days": row.get(
                "operational_telemetry_retention_days"
            ),
            "updated_at": row.get("updated_at"),
            "updated_by": row.get("updated_by"),
        }

    async def update_retention(
        self,
        *,
        audit_log_retention_days: Optional[int],
        data_retention_days: Optional[int],
        document_retention_days: Optional[int],
        backup_retention_days: Optional[int],
        operational_telemetry_retention_days: Optional[int] = None,
        updated_by: Optional[str],
    ) -> dict:
        current = await self.get_retention()
        # Phase K fix — `system_settings.setting_value` is NOT NULL; every
        # upsert must carry a value. Store a JSON snapshot of the retention
        # policy (server-authoritative, never invented).
        snapshot = {
            "audit_log_retention_days": audit_log_retention_days
            if audit_log_retention_days is not None
            else current["audit_log_retention_days"],
            "data_retention_days": data_retention_days
            if data_retention_days is not None
            else current["data_retention_days"],
            "document_retention_days": document_retention_days
            if document_retention_days is not None
            else current["document_retention_days"],
            "backup_retention_days": backup_retention_days
            if backup_retention_days is not None
            else current["backup_retention_days"],
            "operational_telemetry_retention_days": operational_telemetry_retention_days
            if operational_telemetry_retention_days is not None
            else current["operational_telemetry_retention_days"],
        }
        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                audit_log_retention_days, data_retention_days,
                document_retention_days, backup_retention_days,
                operational_telemetry_retention_days,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'retention',
                'Configurable platform data-retention policy (N3)',
                $2::jsonb,
                $3, $4, $5, $6, $7, $8, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                audit_log_retention_days = EXCLUDED.audit_log_retention_days,
                data_retention_days = EXCLUDED.data_retention_days,
                document_retention_days = EXCLUDED.document_retention_days,
                backup_retention_days = EXCLUDED.backup_retention_days,
                operational_telemetry_retention_days = EXCLUDED.operational_telemetry_retention_days,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_RETENTION_COLUMNS}
            """,
            _SETTINGS_KEY,
            dumps_jsonb(snapshot),
            audit_log_retention_days if audit_log_retention_days is not None else current["audit_log_retention_days"],
            data_retention_days if data_retention_days is not None else current["data_retention_days"],
            document_retention_days if document_retention_days is not None else current["document_retention_days"],
            backup_retention_days if backup_retention_days is not None else current["backup_retention_days"],
            operational_telemetry_retention_days
            if operational_telemetry_retention_days is not None
            else current["operational_telemetry_retention_days"],
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return {
            "audit_log_retention_days": row.get("audit_log_retention_days"),
            "data_retention_days": row.get("data_retention_days"),
            "document_retention_days": row.get("document_retention_days"),
            "backup_retention_days": row.get("backup_retention_days"),
            "operational_telemetry_retention_days": row.get(
                "operational_telemetry_retention_days"
            ),
            "updated_at": row.get("updated_at"),
            "updated_by": row.get("updated_by"),
        }

    # AbstractRepository contract (this repository is method-driven).
    async def get(self, id: str) -> Optional[dict]:
        return await self.get_retention() if id == _SETTINGS_KEY else None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None

    # -----------------------------------------------------------------
    # Analytics & Integrations (GA4 only)
    # -----------------------------------------------------------------

    async def get_analytics(self) -> dict:
        """Return the Analytics & Integrations configuration.

        Provider configuration lives in the generic ``setting_value`` JSONB
        column, so adding a provider needs no schema change. A missing row
        yields the fail-closed default (disabled, no measurement ID).
        """
        row = await self._fetch_one(
            f"""
            SELECT {_ANALYTICS_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _ANALYTICS_KEY,
        )
        return _analytics_from_row(row)

    async def update_analytics(
        self,
        *,
        enabled: bool,
        ga4_measurement_id: Optional[str],
        updated_by: Optional[str],
    ) -> dict:
        """Persist the Analytics & Integrations configuration."""
        snapshot = {
            "enabled": bool(enabled),
            "ga4_measurement_id": ga4_measurement_id,
        }
        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'analytics_integrations',
                'Analytics & Integrations provider configuration (Google Analytics 4)',
                $2::jsonb, $3, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description,
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_ANALYTICS_COLUMNS}
            """,
            _ANALYTICS_KEY,
            dumps_jsonb(snapshot),
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return _analytics_from_row(row)
