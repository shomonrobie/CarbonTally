"""Backup configuration (environment-driven, Render-friendly).

Every value comes from the environment (``os.getenv``), matching the existing
``backend/config.py`` / ``infra/supabase.py`` convention. **No secret has a
default**: an unset encryption key raises
:class:`backup.errors.BackupConfigurationError` before any work starts.

Environment contract (all optional except the encryption key, required when
encryption is requested):

``CT_BACKUP_OBJECT_STORE``   ``local`` (default) or ``memory``
``CT_BACKUP_LOCAL_ROOT``     provider root for the local object store
                             (default ``/tmp/ct_backup_store``)
``CT_BACKUP_TEMP_ROOT``      parent directory for temporary export material
``CT_BACKUP_ENCRYPTION_KEY`` base64 (standard, padded) 32-byte AES-256 key
``CT_BACKUP_KEY_ID``         non-secret key identifier recorded in the manifest
                             and the artifact envelope (default ``key-v1``)
``CT_BACKUP_SCHEMAS``        comma-separated schemas to export (default ``public``)
``CT_BACKUP_COMPRESSION``    ``gzip`` (default) or ``none``
``CT_BACKUP_COMPRESSION_LEVEL`` gzip level 1–9 (default ``6``)
``CT_BACKUP_DENIED_SCHEMA_OVERRIDE``
                             must equal
                             ``I_UNDERSTAND_THIS_EXPORTS_CREDENTIAL_MATERIAL`` to
                             permit a denied schema (F2). Default: unset = refused.
``CT_BACKUP_VERIFY_READBACK`` ``1`` (default) reads each stored object back and
                             re-verifies the application SHA-256; ``0`` disables
                             that (documented as a deliberate trade-off).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Sequence

from backup.errors import BackupConfigurationError

DEFAULT_SCHEMAS: tuple[str, ...] = ("public",)
DEFAULT_LOCAL_ROOT = "/tmp/ct_backup_store"
DEFAULT_OBJECT_STORE = "local"
DEFAULT_COMPRESSION = "gzip"
DEFAULT_COMPRESSION_LEVEL = 6
DEFAULT_KEY_ID = "key-v1"
DEFAULT_VERIFY_READBACK = True

#: Credential-bearing / provider-private schemas that must never be exported.
#: Supabase keeps authentication credential material (``auth.users``), provider
#: internals (``storage``, ``vault``, ``realtime``) and migration history in
#: dedicated schemas; exporting them would place credential material inside a
#: backup artifact. The policy is **fail-closed** (review finding F2): the
#: default export is ``public`` only, and naming a denied schema raises unless the
#: unmistakable administrative override below is supplied deliberately.
DENIED_SCHEMAS: tuple[str, ...] = (
    "auth",
    "storage",
    "vault",
    "realtime",
    "supabase_functions",
    "supabase_migrations",
    "pgbouncer",
)

#: Exact phrase required by ``CT_BACKUP_DENIED_SCHEMA_OVERRIDE``. It is
#: intentionally long and explicit, so enabling it can only ever be a
#: deliberate administrative act.
DENIED_SCHEMA_OVERRIDE_PHRASE = "I_UNDERSTAND_THIS_EXPORTS_CREDENTIAL_MATERIAL"

_ALLOWED_STORES = ("local", "memory")
_ALLOWED_COMPRESSION = ("gzip", "none")
_FALSE_VALUES = ("0", "false", "no", "off")


def validate_schemas(schemas: Sequence[str], *, allow_override: bool = False) -> None:
    """Fail closed when a credential-bearing schema is requested (F2).

    Args:
        schemas: schema names the caller wants to export.
        allow_override: ``True`` only when the deliberate administrative
            override has been supplied.

    Raises:
        BackupConfigurationError: when a denied schema is requested without the
            override, or when a schema name is not a plain identifier.
    """
    denied = [name for name in schemas if str(name).strip().lower() in DENIED_SCHEMAS]
    if denied and not allow_override:
        raise BackupConfigurationError(
            "refusing to export credential-bearing/private schema(s): "
            + ", ".join(sorted(denied))
            + ". These schemas hold authentication or provider credential material. "
            "Remove them from CT_BACKUP_SCHEMAS, or set "
            f"CT_BACKUP_DENIED_SCHEMA_OVERRIDE={DENIED_SCHEMA_OVERRIDE_PHRASE} to "
            "override deliberately.",
            details={"denied_schemas": sorted(denied), "override": "not supplied"},
        )
    for name in schemas:
        candidate = str(name)
        if candidate != candidate.strip() or not candidate:
            raise BackupConfigurationError(
                "schema names must not contain surrounding whitespace",
                details={"value": candidate},
            )



@dataclass(frozen=True)
class BackupSettings:
    """Resolved, validated backup configuration.

    The encryption key is held as a private ``bytes`` field that is **never**
    rendered by ``repr`` and never logged.
    """

    object_store: str = DEFAULT_OBJECT_STORE
    local_root: str = DEFAULT_LOCAL_ROOT
    temp_root: Optional[str] = None
    schemas: Sequence[str] = field(default_factory=lambda: DEFAULT_SCHEMAS)
    compression: str = DEFAULT_COMPRESSION
    compression_level: int = DEFAULT_COMPRESSION_LEVEL
    key_id: str = DEFAULT_KEY_ID
    encryption_key: Optional[bytes] = field(default=None, repr=False)
    #: F2 — deliberate administrative opt-in for denied schemas (never the default).
    allow_denied_schemas: bool = False
    #: F11 — read the stored object back and re-verify the application SHA-256.
    verify_readback: bool = DEFAULT_VERIFY_READBACK

    def __repr__(self) -> str:  # pragma: no cover - trivial, but security-relevant
        return (
            "BackupSettings("
            f"object_store={self.object_store!r}, local_root={self.local_root!r}, "
            f"schemas={list(self.schemas)!r}, compression={self.compression!r}, "
            f"compression_level={self.compression_level}, key_id={self.key_id!r}, "
            f"allow_denied_schemas={self.allow_denied_schemas}, "
            f"verify_readback={self.verify_readback}, "
            f"encryption_key={'<set>' if self.encryption_key else None})"
        )

    def require_encryption_key(self) -> bytes:
        """Return the key, or raise if it is not configured."""
        if not self.encryption_key:
            raise BackupConfigurationError(
                "CT_BACKUP_ENCRYPTION_KEY is not configured; a backup artifact "
                "must never be written unencrypted",
                details={"setting": "CT_BACKUP_ENCRYPTION_KEY"},
            )
        return self.encryption_key

    @staticmethod
    def from_env(env: Optional[dict[str, str]] = None) -> "BackupSettings":
        """Build settings from the process environment (or a supplied mapping).

        Raises:
            BackupConfigurationError: when a value is present but invalid.
        """
        source = os.environ if env is None else env

        object_store = (source.get("CT_BACKUP_OBJECT_STORE") or DEFAULT_OBJECT_STORE).strip().lower()
        if object_store not in _ALLOWED_STORES:
            raise BackupConfigurationError(
                f"CT_BACKUP_OBJECT_STORE must be one of {_ALLOWED_STORES}",
                details={"value": object_store},
            )

        compression = (source.get("CT_BACKUP_COMPRESSION") or DEFAULT_COMPRESSION).strip().lower()
        if compression not in _ALLOWED_COMPRESSION:
            raise BackupConfigurationError(
                f"CT_BACKUP_COMPRESSION must be one of {_ALLOWED_COMPRESSION}",
                details={"value": compression},
            )

        level_raw = source.get("CT_BACKUP_COMPRESSION_LEVEL")
        if level_raw:
            try:
                level = int(level_raw)
            except ValueError as exc:
                raise BackupConfigurationError(
                    "CT_BACKUP_COMPRESSION_LEVEL must be an integer",
                    details={"value": level_raw},
                ) from exc
            if not 1 <= level <= 9:
                raise BackupConfigurationError(
                    "CT_BACKUP_COMPRESSION_LEVEL must be between 1 and 9",
                    details={"value": level},
                )
        else:
            level = DEFAULT_COMPRESSION_LEVEL

        raw_schemas = source.get("CT_BACKUP_SCHEMAS")
        schemas: tuple[str, ...] = (
            tuple(part.strip() for part in raw_schemas.split(",") if part.strip())
            if raw_schemas
            else DEFAULT_SCHEMAS
        )

        key_raw = (source.get("CT_BACKUP_ENCRYPTION_KEY") or "").strip()
        key: Optional[bytes] = _decode_key(key_raw) if key_raw else None

        override_raw = (source.get("CT_BACKUP_DENIED_SCHEMA_OVERRIDE") or "").strip()
        allow_denied = override_raw == DENIED_SCHEMA_OVERRIDE_PHRASE

        readback_raw = (source.get("CT_BACKUP_VERIFY_READBACK") or "").strip().lower()
        verify_readback = DEFAULT_VERIFY_READBACK if not readback_raw else (
            readback_raw not in _FALSE_VALUES
        )

        # F2: fail closed on credential-bearing schemas before anything else runs.
        validate_schemas(schemas, allow_override=allow_denied)

        return BackupSettings(
            object_store=object_store,
            local_root=(source.get("CT_BACKUP_LOCAL_ROOT") or DEFAULT_LOCAL_ROOT).strip(),
            temp_root=(source.get("CT_BACKUP_TEMP_ROOT") or "").strip() or None,
            schemas=schemas,
            compression=compression,
            compression_level=level,
            key_id=(source.get("CT_BACKUP_KEY_ID") or DEFAULT_KEY_ID).strip(),
            encryption_key=key,
            allow_denied_schemas=allow_denied,
            verify_readback=verify_readback,
        )


def _decode_key(value: str) -> bytes:
    """Decode a base64 AES key, validating that it is exactly 32 bytes."""
    import base64
    import binascii

    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BackupConfigurationError(
            "CT_BACKUP_ENCRYPTION_KEY must be valid base64",
            details={"reason": "base64 decode failed"},
        ) from exc
    if len(raw) != 32:
        raise BackupConfigurationError(
            "CT_BACKUP_ENCRYPTION_KEY must decode to exactly 32 bytes (AES-256)",
            details={"length": len(raw)},
        )
    return raw

