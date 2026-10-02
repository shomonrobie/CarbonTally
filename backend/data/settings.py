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

#: Fixed key for the notification configuration row (CT-FINAL-01 notifications).
_NOTIFICATION_KEY = "platform_notifications"

_NOTIFICATION_COLUMNS = "setting_value, updated_at, updated_by"

#: Fixed key for the CT-FINAL-01 upload-policy row (Admin Panel → Upload Policy).
_UPLOAD_POLICY_KEY = "upload_policy"

_UPLOAD_POLICY_COLUMNS = "setting_value, updated_at, updated_by"

#: Fixed key for the CT-FINAL-02 email delivery provider row (EMAIL-CONFIG-01).
#: The row stores the provider selection and the NAME of the environment
#: variable holding the credential — never the credential itself.
_EMAIL_PROVIDER_KEY = "email_provider"

_EMAIL_PROVIDER_COLUMNS = "setting_value, updated_at, updated_by"

#: Fixed key for the BACKUP-02 operational policy row (architecture §16 / §9).
#: This row is **configuration only**: the mandatory security properties
#: (encryption, private storage, authorization, tenant isolation, integrity
#: verification) are enforced in code and cannot be expressed here at all.
#: Retention is deliberately NOT stored here — it stays in the existing
#: ``backup_retention_days`` column so there is exactly one source of truth.
_BACKUP_POLICY_KEY = "backup_policy"

_BACKUP_POLICY_COLUMNS = "setting_value, updated_at, updated_by"


def _backup_policy_from_row(row: Optional[Any]) -> dict:
    """Map a ``system_settings`` row to the backup-policy configuration shape.

    Only the allow-listed keys are surfaced: a hand-edited row can never inject a
    field the API would then honour, and a malformed payload degrades to "not
    configured" rather than raising on a settings read.
    """
    from backup.policy import POLICY_FIELDS

    try:
        value = loads_jsonb(row.get("setting_value")) if row is not None else None
    except (TypeError, ValueError):
        value = None
    if not isinstance(value, dict):
        value = {}
    policy = {field: value.get(field) for field in POLICY_FIELDS}
    return {
        **policy,
        "updated_at": row.get("updated_at") if row is not None else None,
        "updated_by": row.get("updated_by") if row is not None else None,
    }

#: Sentinel meaning "the caller did not supply this field".  An explicit
#: ``None`` clears a field instead — an administrator must be able to remove an
#: SMTP transport that is no longer used, and clearing must never silently
#: restore the previous value (see ``update_email_provider``).
_UNSET: Any = object()


def _upload_policy_from_row(row: Optional[Any]) -> dict:
    """Map a ``system_settings`` row to the upload-policy configuration shape.

    A missing row, an unparseable payload or a malformed value yields ``None``
    for that field: the effective limit is then the documented default
    (``utils.upload_limits.effective_policy``), never an invented value and
    never "unlimited".  Unknown keys in a stored payload are ignored — an
    operator can never smuggle an unrelated limit in through this row.
    """
    from utils.upload_limits import POLICY_FIELDS

    try:
        value = loads_jsonb(row.get("setting_value")) if row is not None else None
    except (TypeError, ValueError):
        value = None
    if not isinstance(value, dict):
        value = {}
    policy = {field: value.get(field) for field in POLICY_FIELDS}
    return {
        **policy,
        "updated_at": row.get("updated_at") if row is not None else None,
        "updated_by": row.get("updated_by") if row is not None else None,
    }


def _notification_from_row(row: Optional[Any]) -> dict:
    """Map a ``system_settings`` row to the notification configuration shape.

    A missing row, an unparseable payload or a malformed value fails closed to
    "not configured": the effective sender is then the platform default
    (``services.email_sender.resolve_email_sender``), never an invented address.
    """
    try:
        value = loads_jsonb(row.get("setting_value")) if row is not None else None
    except (TypeError, ValueError):
        value = None
    if not isinstance(value, dict):
        value = {}
    sender = value.get("email_sender")
    if not isinstance(sender, str) or not sender.strip():
        sender = None
    return {
        "email_sender": sender,
        "updated_at": row.get("updated_at") if row is not None else None,
        "updated_by": row.get("updated_by") if row is not None else None,
    }



def _email_provider_from_row(row: Optional[Any]) -> dict:
    """Map a ``system_settings`` row to the email-provider configuration shape.

    A missing row, an unparseable payload or a malformed value fails closed to
    the documented default provider: the runtime then uses ``resend`` with the
    ``RESEND_API_KEY`` environment credential, exactly as an unconfigured
    deployment does today.  A credential *value* is never read: the payload can
    only ever contain the referenced environment variable name.
    """
    from services.email_provider import ALLOWED_CREDENTIAL_ENVS, PROVIDER_FIELDS

    try:
        value = loads_jsonb(row.get("setting_value")) if row is not None else None
    except (TypeError, ValueError):
        value = None
    if not isinstance(value, dict):
        value = {}
    config = {field: value.get(field) for field in PROVIDER_FIELDS}
    # Defence in depth: a manually edited row can never widen the credential
    # variable set beyond the allow-list.
    credential_env = config.get("credential_env")
    if isinstance(credential_env, str) and credential_env not in ALLOWED_CREDENTIAL_ENVS:
        config["credential_env"] = None
    return {
        **config,
        "updated_at": row.get("updated_at") if row is not None else None,
        "updated_by": row.get("updated_by") if row is not None else None,
    }


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

    # -----------------------------------------------------------------
    # Notifications — platform email sender (CT-FINAL-01)
    # -----------------------------------------------------------------

    async def get_notification_sender(self) -> dict:
        """Return the configured notification sender (never a credential).

        Provider configuration lives in the generic ``setting_value`` JSONB
        column, so this needs no schema change.  A missing row yields
        ``email_sender = None`` — the caller resolves the platform default.
        """
        row = await self._fetch_one(
            f"""
            SELECT {_NOTIFICATION_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _NOTIFICATION_KEY,
        )
        return _notification_from_row(row)

    async def update_notification_sender(
        self,
        *,
        email_sender: Optional[str],
        updated_by: Optional[str],
    ) -> dict:
        """Persist the platform notification sender.

        The value must already have been validated by
        ``services.email_sender.normalise_email_sender`` (the API layer does
        this), so an unvalidated address can never reach this write.
        """
        snapshot = {"email_sender": email_sender}
        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'notifications',
                'Notification configuration (platform transactional-email sender)',
                $2::jsonb, $3, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description,
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_NOTIFICATION_COLUMNS}
            """,
            _NOTIFICATION_KEY,
            dumps_jsonb(snapshot),
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return _notification_from_row(row)

    # -----------------------------------------------------------------
    # Backup policy — the ONLY configurable backup layer (BACKUP-02 / §16)
    # -----------------------------------------------------------------

    async def get_backup_policy(self) -> dict:
        """Return the stored backup policy (never an invented value).

        A missing row yields ``None`` for every field, so the effective policy is
        computed from the documented defaults plus the retention setting, and
        "not configured" is never presented as a decision somebody made.
        """
        row = await self._fetch_one(
            f"""
            SELECT {_BACKUP_POLICY_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _BACKUP_POLICY_KEY,
        )
        return _backup_policy_from_row(row)

    async def update_backup_policy(
        self,
        *,
        fields: dict,
        updated_by: Optional[str],
    ) -> dict:
        """Persist the backup policy.

        ``fields`` must already have been normalised by
        ``backup.policy.validate_policy_update`` (the API layer does this), so an
        unsupported or invariant-disabling key can never reach this write. Only
        the allow-listed keys are merged; everything else is discarded rather than
        stored and ignored.
        """
        from backup.policy import POLICY_FIELDS

        allowed = {key: value for key, value in dict(fields).items() if key in POLICY_FIELDS}
        current = await self.get_backup_policy()
        snapshot = {
            field: (
                allowed[field]
                if field in allowed
                else current.get(field)
            )
            for field in POLICY_FIELDS
        }
        # Retention is owned by the retention row (single source of truth), so it
        # is never mirrored into this payload.
        snapshot.pop("retention_days", None)
        if not snapshot:
            # A converging no-op: the row must still exist so the admin surface can
            # report who last touched the policy and when.
            snapshot = {}
        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'backup',
                'Backup operational policy (configuration only; security properties are enforced in code)',
                $2::jsonb, $3, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description,
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_BACKUP_POLICY_COLUMNS}
            """,
            _BACKUP_POLICY_KEY,
            dumps_jsonb(snapshot),
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return _backup_policy_from_row(row)

    # -----------------------------------------------------------------
    # Upload policy — canonical admin-configurable upload limits (CT-FINAL-01)
    # -----------------------------------------------------------------

    async def get_upload_policy(self) -> dict:
        """Return the configured upload policy (never an invented value).

        A missing row yields ``None`` for every field — the caller applies the
        documented defaults (``utils.upload_limits.effective_policy``).
        """
        row = await self._fetch_one(
            f"""
            SELECT {_UPLOAD_POLICY_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _UPLOAD_POLICY_KEY,
        )
        return _upload_policy_from_row(row)

    async def update_upload_policy(
        self,
        *,
        max_file_size_mb=None,
        max_files_per_batch=None,
        max_batch_size_mb=None,
        updated_by: Optional[str] = None,
    ) -> dict:
        """Persist the upload policy; a ``None`` field keeps its stored value.

        The values must already have been validated by
        ``utils.upload_limits.validate_upload_policy`` (the API layer does
        this), so an out-of-range limit can never reach this write.  The row
        lives in the pre-existing ``system_settings`` table, so no schema
        change is required and the value survives an application restart.
        """
        current = await self.get_upload_policy()
        snapshot = {}
        for field, supplied in (
            ("max_file_size_mb", max_file_size_mb),
            ("max_files_per_batch", max_files_per_batch),
            ("max_batch_size_mb", max_batch_size_mb),
        ):
            snapshot[field] = current.get(field) if supplied is None else supplied

        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'upload_policy',
                'Upload policy (max file size, files per batch, aggregate batch size)',
                $2::jsonb, $3, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description,
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_UPLOAD_POLICY_COLUMNS}
            """,
            _UPLOAD_POLICY_KEY,
            dumps_jsonb(snapshot),
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return _upload_policy_from_row(row)

    # -----------------------------------------------------------------
    # Email delivery provider — CT-FINAL-02 EMAIL-CONFIG-01
    # -----------------------------------------------------------------

    async def get_email_provider(self) -> dict:
        """Return the configured email delivery provider (never a secret).

        A missing row yields ``None`` for every field — the caller applies the
        documented default provider (``services.email_provider``).  Only the
        provider selection and the *name* of the environment variable holding
        the credential are ever stored, so this row can never contain a secret.
        """
        row = await self._fetch_one(
            f"""
            SELECT {_EMAIL_PROVIDER_COLUMNS}
            FROM public.system_settings
            WHERE setting_key = $1
            """,
            _EMAIL_PROVIDER_KEY,
        )
        return _email_provider_from_row(row)

    async def update_email_provider(
        self,
        *,
        provider: Any = _UNSET,
        smtp_host: Any = _UNSET,
        smtp_port: Any = _UNSET,
        smtp_username: Any = _UNSET,
        smtp_use_tls: Any = _UNSET,
        credential_env: Any = _UNSET,
        updated_by: Optional[str] = None,
    ) -> dict:
        """Persist the email delivery provider configuration.

        Values must already be validated by
        ``services.email_provider.normalise_provider_config`` (the API layer
        does this) so an unknown provider or an out-of-policy credential
        variable can never reach this write.  A credential *value* is never
        accepted by this method: only the referenced environment variable name.

        An **omitted** field (left as :data:`_UNSET`) keeps its stored value,
        while an explicit ``None`` clears it — reverting to the stored value on
        an explicit clear would make an unused SMTP transport impossible to
        remove.
        """
        from services.email_provider import normalise_provider_config

        current = await self.get_email_provider()
        merged = {}
        for field, supplied in (
            ("provider", provider),
            ("smtp_host", smtp_host),
            ("smtp_port", smtp_port),
            ("smtp_username", smtp_username),
            ("smtp_use_tls", smtp_use_tls),
            ("credential_env", credential_env),
        ):
            merged[field] = current.get(field) if supplied is _UNSET else supplied
        snapshot = normalise_provider_config(merged)

        row = await self._fetch_one(
            f"""
            INSERT INTO public.system_settings (
                setting_key, setting_type, description, setting_value,
                updated_by, updated_at, created_at
            )
            VALUES (
                $1, 'email_provider',
                'Email delivery provider selection (credentials live in the environment)',
                $2::jsonb, $3, NOW(), NOW()
            )
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_type = EXCLUDED.setting_type,
                description = EXCLUDED.description,
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING {_EMAIL_PROVIDER_COLUMNS}
            """,
            _EMAIL_PROVIDER_KEY,
            dumps_jsonb(snapshot),
            updated_by,
        )
        if row is None:
            raise RuntimeError("system_settings upsert returned no row")
        return _email_provider_from_row(row)
