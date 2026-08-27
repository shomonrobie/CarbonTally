"""Platform settings repository (N3 — configurable retention).

Retention is a CONFIGURABLE product capability (N3). The RC2
``system_settings`` table already carries the retention columns
(``audit_log_retention_days``, ``data_retention_days``,
``document_retention_days``, ``backup_retention_days``) — this repository reads
and writes those columns and never invents policy values: unset values are
returned as ``None`` so the UI shows "not configured" rather than a fabricated
duration.

Enforcement is a server-side concern (N3); this surface is configuration only.
"""

from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

#: Fixed key for the single system_settings row this repository manages.
_SETTINGS_KEY = "platform_retention"

_RETENTION_COLUMNS = (
    "audit_log_retention_days, data_retention_days, document_retention_days, "
    "backup_retention_days, updated_at, updated_by"
)


class SettingsRepository(AbstractRepository[dict]):
    """Read/update the platform retention configuration row."""

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
                "updated_at": None,
                "updated_by": None,
            }
        return {
            "audit_log_retention_days": row.get("audit_log_retention_days"),
            "data_retention_days": row.get("data_retention_days"),
            "document_retention_days": row.get("document_retention_days"),
            "backup_retention_days": row.get("backup_retention_days"),
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
        updated_by: Optional[str],
    ) -> dict:
        current = await self.get_retention()
        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description,
                audit_log_retention_days, data_retention_days,
                document_retention_days, backup_retention_days,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'retention',
                'Configurable platform data-retention policy (N3)',
                $2, $3, $4, $5, $6, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                audit_log_retention_days = EXCLUDED.audit_log_retention_days,
                data_retention_days = EXCLUDED.data_retention_days,
                document_retention_days = EXCLUDED.document_retention_days,
                backup_retention_days = EXCLUDED.backup_retention_days,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_RETENTION_COLUMNS}
            """,
            _SETTINGS_KEY,
            audit_log_retention_days if audit_log_retention_days is not None else current["audit_log_retention_days"],
            data_retention_days if data_retention_days is not None else current["data_retention_days"],
            document_retention_days if document_retention_days is not None else current["document_retention_days"],
            backup_retention_days if backup_retention_days is not None else current["backup_retention_days"],
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return {
            "audit_log_retention_days": row.get("audit_log_retention_days"),
            "data_retention_days": row.get("data_retention_days"),
            "document_retention_days": row.get("document_retention_days"),
            "backup_retention_days": row.get("backup_retention_days"),
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
